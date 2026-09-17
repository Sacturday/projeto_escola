from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import exigir_acesso_escola, get_current_user_websocket

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, escola_id: int):
        await websocket.accept()
        self.rooms[escola_id].append(websocket)

    def disconnect(self, websocket: WebSocket, escola_id: int):
        if websocket in self.rooms.get(escola_id, []):
            self.rooms[escola_id].remove(websocket)
        if not self.rooms.get(escola_id):
            self.rooms.pop(escola_id, None)

    async def broadcast_to_escola(self, escola_id: int, message: str):
        desconectados = []
        for ws in self.rooms.get(escola_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                desconectados.append(ws)
        for ws in desconectados:
            self.disconnect(ws, escola_id)


websocket_manager = ConnectionManager()


@router.websocket("/ws/dashboard/{escola_id}")
async def dashboard_ws(
    websocket: WebSocket,
    escola_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        usuario = await get_current_user_websocket(websocket, db)
        exigir_acesso_escola(usuario, escola_id)
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket_manager.connect(websocket, escola_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, escola_id)
