from typing import Dict, List, Optional
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # 使用字典来存储活跃的连接，键为 user_id，值为 WebSocket 对象
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """
        接受新的WebSocket连接并将其与用户ID关联。
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"用户 {user_id} 的WebSocket已连接。当前在线人数: {len(self.active_connections)}")

    def disconnect(self, user_id: int):
        """
        断开指定用户的WebSocket连接。
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"用户 {user_id} 的WebSocket已断开。当前在线人数: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, user_id: int):
        """
        向指定用户发送个人消息。
        """
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        """
        向所有在线用户广播消息。
        通过为每个发送操作添加 try-except 块来增强健壮性，
        以防止单个断开的连接中断整个广播。
        """
        # 创建一个要迭代的连接列表副本，以防在迭代期间 active_connections 发生变化
        connections_to_broadcast = list(self.active_connections.values())
        for connection in connections_to_broadcast:
            try:
                await connection.send_text(message)
            except Exception as e:
                # 如果发送失败（例如，连接已意外关闭），则打印错误但继续
                print(f"向某个客户端广播消息时出错: {e}")

# 创建一个ConnectionManager的全局单例
# 这样在整个应用中，我们都将使用这同一个管理器实例
manager = ConnectionManager() 