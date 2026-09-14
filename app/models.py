from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_name = Column(String(64), unique=True, index=True, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_wifi_rssi = Column(Integer, nullable=True)

    readings = relationship("Reading", back_populates="device", cascade="all, delete-orphan")


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)

    # Server-side receipt time (authoritative for ordering/charting)
    server_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    # Device's own millis()-based clock, kept only for reference/debugging
    device_timestamp_ms = Column(Integer, nullable=True)

    spo2 = Column(Float, nullable=True)
    bpm_avg = Column(Float, nullable=True)
    bpm_valid = Column(Boolean, default=False)

    temp_c = Column(Float, nullable=True)
    temp_valid = Column(Boolean, default=False)

    finger_on_sensor = Column(Boolean, default=False)
    raw_red = Column(Integer, nullable=True)
    raw_ir = Column(Integer, nullable=True)
    wifi_rssi = Column(Integer, nullable=True)

    device = relationship("Device", back_populates="readings")


Index("ix_readings_device_time", Reading.device_id, Reading.server_timestamp)
