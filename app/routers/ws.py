from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    """
    Frontend connects here to receive every new reading the instant it's
    POSTed by the ESP32, instead of polling /api/readings on a timer.

    Message shape: {"type": "reading", "data": <ReadingOut fields>}
    """
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect client -> server messages, but reading keeps
            # the connection alive and lets us detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
