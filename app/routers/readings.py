from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Device, Reading
from app.schemas import ReadingIn, ReadingOut, ReadingsPage
from app.security import require_auth
from app.config import settings
from app.ws_manager import manager

router = APIRouter(prefix="/api/readings", tags=["readings"])


def _get_or_create_device(db: Session, device_name: str) -> Device:
    device = db.query(Device).filter(Device.device_name == device_name).first()
    if device is None:
        device = Device(device_name=device_name)
        db.add(device)
        db.commit()
        db.refresh(device)
    return device


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ReadingOut)
async def create_reading(
    body: ReadingIn,
    db: Session = Depends(get_db),
    _subject: str = Depends(require_auth),
):
    """
    Device-facing endpoint. Body matches sendToBackend()'s JSON payload
    exactly (field-for-field), so the firmware needs no changes.
    Requires the Bearer token returned by /api/auth/login.
    """
    device = _get_or_create_device(db, body.device_name)
    device.last_seen = datetime.utcnow()
    if body.wifi_rssi is not None:
        device.last_wifi_rssi = body.wifi_rssi

    reading = Reading(
        device_id=device.id,
        device_timestamp_ms=body.device_timestamp_ms,
        spo2=body.spo2,
        bpm_avg=body.bpm_avg,
        bpm_valid=body.bpm_valid,
        temp_c=body.temp_C,
        temp_valid=body.temp_valid,
        finger_on_sensor=body.finger_on_sensor,
        raw_red=body.raw_red,
        raw_ir=body.raw_ir,
        wifi_rssi=body.wifi_rssi,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    out = ReadingOut(
        id=reading.id,
        device_name=device.device_name,
        server_timestamp=reading.server_timestamp,
        device_timestamp_ms=reading.device_timestamp_ms,
        spo2=reading.spo2,
        bpm_avg=reading.bpm_avg,
        bpm_valid=reading.bpm_valid,
        temp_c=reading.temp_c,
        temp_valid=reading.temp_valid,
        finger_on_sensor=reading.finger_on_sensor,
        raw_red=reading.raw_red,
        raw_ir=reading.raw_ir,
        wifi_rssi=reading.wifi_rssi,
    )

    # Push straight to any connected dashboards so charts update in real time.
    await manager.broadcast({"type": "reading", "data": out.model_dump(mode="json")})

    return out


@router.get("", response_model=ReadingsPage)
def list_readings(
    device_name: str = Query(..., description="Device name to fetch readings for"),
    limit: int = Query(100, le=settings.MAX_READINGS_RETURNED),
    db: Session = Depends(get_db),
):
    """Frontend-facing endpoint: history for charting. No auth required by default."""
    device = db.query(Device).filter(Device.device_name == device_name).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Unknown device_name")

    rows = (
        db.query(Reading)
        .filter(Reading.device_id == device.id)
        .order_by(desc(Reading.server_timestamp))
        .limit(limit)
        .all()
    )
    rows.reverse()  # oldest -> newest, convenient for charting

    readings = [
        ReadingOut(
            id=r.id,
            device_name=device.device_name,
            server_timestamp=r.server_timestamp,
            device_timestamp_ms=r.device_timestamp_ms,
            spo2=r.spo2,
            bpm_avg=r.bpm_avg,
            bpm_valid=r.bpm_valid,
            temp_c=r.temp_c,
            temp_valid=r.temp_valid,
            finger_on_sensor=r.finger_on_sensor,
            raw_red=r.raw_red,
            raw_ir=r.raw_ir,
            wifi_rssi=r.wifi_rssi,
        )
        for r in rows
    ]
    return ReadingsPage(device_name=device.device_name, count=len(readings), readings=readings)


@router.get("/latest", response_model=Optional[ReadingOut])
def latest_reading(device_name: str = Query(...), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_name == device_name).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Unknown device_name")

    r = (
        db.query(Reading)
        .filter(Reading.device_id == device.id)
        .order_by(desc(Reading.server_timestamp))
        .first()
    )
    if r is None:
        return None

    return ReadingOut(
        id=r.id,
        device_name=device.device_name,
        server_timestamp=r.server_timestamp,
        device_timestamp_ms=r.device_timestamp_ms,
        spo2=r.spo2,
        bpm_avg=r.bpm_avg,
        bpm_valid=r.bpm_valid,
        temp_c=r.temp_c,
        temp_valid=r.temp_valid,
        finger_on_sensor=r.finger_on_sensor,
        raw_red=r.raw_red,
        raw_ir=r.raw_ir,
        wifi_rssi=r.wifi_rssi,
    )
