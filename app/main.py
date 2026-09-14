import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.routers import auth, readings, devices, ws

# Create tables on startup (fine for SQLite/small Postgres; swap for Alembic
# migrations if the schema starts changing often).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MedMon Backend",
    description="Backend for the ESP32 Clinical-Grade IoT Medical Monitor firmware.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(readings.router)
app.include_router(devices.router)
app.include_router(ws.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve the dashboard at /dashboard (frontend/index.html talks to the API
# above via fetch() + the /ws/live WebSocket).
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/dashboard", StaticFiles(directory=_frontend_dir, html=True), name="dashboard")


@app.get("/")
def root():
    return {
        "service": "medmon-backend",
        "dashboard": "/dashboard",
        "docs": "/docs",
    }
