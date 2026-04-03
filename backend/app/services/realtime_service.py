from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class RealtimeConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, payload: dict[str, Any]) -> None:
        sockets = list(self._connections.get(user_id, set()))
        stale: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)

        for websocket in stale:
            self.disconnect(user_id, websocket)

    async def send_to_users(self, user_ids: list[int], payload: dict[str, Any]) -> None:
        sent: set[int] = set()
        for user_id in user_ids:
            if user_id in sent:
                continue
            sent.add(user_id)
            await self.send_to_user(user_id, payload)


realtime_manager = RealtimeConnectionManager()
