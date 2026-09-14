"""
FastAPI backend for the ESP32 + RC522 RFID Inventory Scanner
--------------------------------------------------------------
Endpoints:
  POST /scan          <- called BY the ESP32 (sendScan() in the sketch)
  GET  /api/scans      <- called BY the frontend dashboard (polling)
  GET  /api/stations   <- list of distinct station_ids seen so far
  GET  /                <- serves the visualization dashboard (static/index.html)

Run locally with Docker:
    docker build -t rfid-backend .
    docker run -p 8000:8000 rfid-backend

Deployed on Render, the URL becomes https://<your-service>.onrender.com
Set the ESP32's "Backend Server URL" field to:
    https://<your-service>.onrender.com/scan
(NOTE: Render is HTTPS-only — the ESP32 sketch needs the WiFiClientSecure
 patch described in the README, or the POST will fail.)
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ---------- CONFIG ----------
# On Render, set DATA_DIR=/var/data and attach a persistent disk mounted there,
# otherwise the SQLite file is wiped on every deploy/restart.
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "scans.db"

# Must match the X-API-Key header the ESP32 sends (see sendScan() in the sketch).
# On Render, set DEVICE_API_KEY in the dashboard's Environment tab.
VALID_API_KEYS = {os.environ.get("DEVICE_API_KEY", "change-me-device-key")}
# -----------------------------

app = FastAPI(title="RFID Inventory Backend")

# Allow the dashboard (and any other frontend) to call the API from a browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                station_id TEXT NOT NULL,
                received_at TEXT NOT NULL
            )
            """
        )


init_db()


class ScanIn(BaseModel):
    uid: str
    station_id: str


@app.post("/scan")
def receive_scan(scan: ScanIn, x_api_key: str | None = Header(default=None)):
    """Matches the ESP32's sendScan(): POST body {"uid": "...", "station_id": "..."}"""
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO scans (uid, station_id, received_at) VALUES (?, ?, ?)",
            (scan.uid, scan.station_id, now),
        )

    return {"status": "ok", "uid": scan.uid, "station_id": scan.station_id, "received_at": now}


@app.get("/api/scans")
def list_scans(limit: int = 100, station_id: str | None = None):
    """Used by the dashboard to poll for recent scans."""
    with get_db() as conn:
        if station_id:
            rows = conn.execute(
                "SELECT * FROM scans WHERE station_id = ? ORDER BY id DESC LIMIT ?",
                (station_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/stations")
def list_stations():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT station_id, COUNT(*) as scan_count, MAX(received_at) as last_seen "
            "FROM scans GROUP BY station_id ORDER BY last_seen DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}


# Serve the dashboard frontend at "/"
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
