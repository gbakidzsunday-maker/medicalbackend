from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device
from app.schemas import DeviceOut

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
def list_devices(db: Session = Depends(get_db)):
    return db.query(Device).order_by(Device.last_seen.desc()).all()
