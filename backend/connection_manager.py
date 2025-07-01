from typing import Dict, List, Optional
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # 使用字典来存储活跃的连接，键是用户ID，值是WebSocket对象
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """
        接受新的WebSocket连接并将其与用户ID关联。
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        """
        断开指定用户的WebSocket连接。
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        """
        向指定用户发送个人消息。
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str, disconnected_user_id: Optional[int] = None):
        """
        向所有连接的客户端广播消息,可以排除指定用户。
        """
        for user_id, connection in self.active_connections.items():
            if user_id != disconnected_user_id:
                await connection.send_text(message)

# 创建一个ConnectionManager的全局单例
# 这样在整个应用中，我们都将使用这同一个管理器实例
manager = ConnectionManager() 