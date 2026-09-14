from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# --- Auth ---

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Readings ---
# Field names mirror exactly what sendToBackend() in the firmware serializes,
# so the ESP32's JSON body can be parsed directly with no translation layer.

class ReadingIn(BaseModel):
    device_name: str
    temp_C: Optional[float] = 0.0
    temp_valid: Optional[bool] = False
    spo2: Optional[float] = 0.0
    finger_on_sensor: Optional[bool] = False
    bpm_avg: Optional[float] = 0.0
    bpm_valid: Optional[bool] = False
    raw_red: Optional[int] = None
    raw_ir: Optional[int] = None
    wifi_rssi: Optional[int] = None
    device_timestamp_ms: Optional[int] = None


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_name: str
    server_timestamp: datetime
    device_timestamp_ms: Optional[int]
    spo2: Optional[float]
    bpm_avg: Optional[float]
    bpm_valid: bool
    temp_c: Optional[float]
    temp_valid: bool
    finger_on_sensor: bool
    raw_red: Optional[int]
    raw_ir: Optional[int]
    wifi_rssi: Optional[int]


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_name: str
    first_seen: datetime
    last_seen: datetime
    last_wifi_rssi: Optional[int]


class ReadingsPage(BaseModel):
    device_name: str
    count: int
    readings: List[ReadingOut]
