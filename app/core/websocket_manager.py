"""WebSocket connection manager for real-time chat."""

import logging
from collections import defaultdict
from fastapi import WebSocket

logger = logging.getLogger("teamteam")


class ConnectionManager:
    """채팅방별 WebSocket 연결을 관리합니다."""

    def __init__(self) -> None:
        # room_id -> {user_id: WebSocket}
        self._rooms: dict[int, dict[int, WebSocket]] = defaultdict(dict)

    async def connect(self, room_id: int, user_id: int, websocket: WebSocket) -> None:
        """클라이언트를 채팅방에 연결합니다."""
        await websocket.accept()
        self._rooms[room_id][user_id] = websocket
        logger.info(
            f"WebSocket connected: room_id={room_id}, user_id={user_id}, "
            f"active_connections={len(self._rooms[room_id])}"
        )

    def disconnect(self, room_id: int, user_id: int) -> None:
        """클라이언트 연결을 해제합니다."""
        room = self._rooms.get(room_id)
        if room and user_id in room:
            del room[user_id]
            if not room:
                del self._rooms[room_id]
        logger.info(f"WebSocket disconnected: room_id={room_id}, user_id={user_id}")

    async def broadcast(self, room_id: int, message: dict, exclude_user_id: int | None = None) -> None:
        """채팅방의 모든 연결에 메시지를 브로드캐스트합니다."""
        room = self._rooms.get(room_id, {})
        dead: list[int] = []
        for uid, ws in room.items():
            if uid == exclude_user_id:
                continue
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"WebSocket send failed for user_id={uid} in room_id={room_id}: {e}")
                dead.append(uid)
        for uid in dead:
            self.disconnect(room_id, uid)

    def active_count(self, room_id: int) -> int:
        """현재 채팅방에 연결된 클라이언트 수를 반환합니다."""
        return len(self._rooms.get(room_id, {}))


# 앱 전역 싱글톤
manager = ConnectionManager()
