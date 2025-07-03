import asyncio
import websockets
import requests
import json
import time
from typing import Dict, Any, Optional

BASE_URL_HTTP = "http://127.0.0.1:8000"
BASE_URL_WS = "ws://127.0.0.1:8000"

# --- 辅助函数 ---
def register_user(username, email, password):
    """注册一个新用户并返回响应。"""
    url = f"{BASE_URL_HTTP}/users/"
    user_data = {
        "username": username, "email": email, "password": password,
        "public_key": f"key_for_{username}"
    }
    headers = {"Content-Type": "application/json"}
    # 清理数据库，确保用户不存在 (仅用于测试)
    # 在实际测试中，更好的做法是使用独立的测试数据库
    # 此处为简化，我们假设可以重复注册或忽略已存在错误
    return requests.post(url, data=json.dumps(user_data), headers=headers)

def login_user(username, password) -> Optional[str]:
    """用户登录并返回访问令牌。"""
    url = f"{BASE_URL_HTTP}/token"
    login_data = {"username": username, "password": password}
    response = requests.post(url, data=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    print(f"登录失败: {response.status_code} {response.text}")
    return None

class WebSocketClient:
    """一个封装了WebSocket连接和消息处理的类。"""
    def __init__(self, token: str, name: str):
        self.uri = f"{BASE_URL_WS}/ws?token={token}"
        self.name = name
        self.ws: Optional[Any] = None
        self.message_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._listen_task: Optional[asyncio.Task] = None

    async def connect(self):
        """建立WebSocket连接并开始监听消息。"""
        try:
            self.ws = await websockets.connect(self.uri)
            self._listen_task = asyncio.create_task(self._listen())
            print(f"  [客户端 {self.name}] ✅ 连接成功")
        except Exception as e:
            print(f"  [客户端 {self.name}] ❌ 连接失败: {e}")
            raise

    async def _listen(self):
        """持续从WebSocket接收消息并放入队列。"""
        if not self.ws: return
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    print(f"  [客户端 {self.name}] 📥 收到JSON消息: {data}")
                    await self.message_queue.put(data)
                except json.JSONDecodeError:
                    print(f"  [客户端 {self.name}] 📥 收到非JSON文本消息: '{message}'")
        except websockets.exceptions.ConnectionClosed:
            print(f"  [客户端 {self.name}] 🔌 连接已关闭")

    async def send_message(self, recipient_username: str, content: str):
        """向指定用户发送消息。"""
        if not self.ws: return
        message = {
            "recipient_username": recipient_username,
            "content": content
        }
        await self.ws.send(json.dumps(message))
        print(f"  [客户端 {self.name}] 📤 向 {recipient_username} 发送消息: '{content}'")

    async def get_message(self, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
        """从队列中获取一条消息，可设置超时。"""
        try:
            return await asyncio.wait_for(self.message_queue.get(), timeout)
        except asyncio.TimeoutError:
            print(f"  [客户端 {self.name}] ⏰ 等待消息超时")
            return None

    async def close(self):
        """关闭WebSocket连接。"""
        if self._listen_task:
            self._listen_task.cancel()
        if self.ws:
            await self.ws.close()

async def main():
    """主测试函数，按顺序执行所有测试场景。"""
    # --- 1. 准备工作：注册和登录用户 ---
    print("--- 准备工作：注册和登录用户 ---")
    user_a_name = f"tester_a_{int(time.time())}"
    user_b_name = f"tester_b_{int(time.time())}"
    user_c_name = f"tester_c_{int(time.time())}"
    password = "testpassword"

    for name in [user_a_name, user_b_name, user_c_name]:
        register_user(name, f"{name}@test.com", password)
    
    token_a = login_user(user_a_name, password)
    token_b = login_user(user_b_name, password)
    token_c = login_user(user_c_name, password)
    assert token_a, "❌ 用户 A 登录失败"
    assert token_b, "❌ 用户 B 登录失败"
    assert token_c, "❌ 用户 C 登录失败"
    print("✅ 所有用户登录成功\n")

    # --- 2. 在线消息转发测试 ---
    print("\n--- 测试场景1：在线消息转发 ---")
    client_a = WebSocketClient(token_a, "A")
    client_b = WebSocketClient(token_b, "B")
    await client_a.connect()
    await client_b.connect()

    # 清理 B 的上线广播消息
    await client_a.get_message() 
    await client_b.get_message()
    await client_b.get_message()

    test_msg_content = "你好 B，在线吗？"
    await client_a.send_message(user_b_name, test_msg_content)
    
    received_msg = await client_b.get_message()
    assert received_msg, "❌ B 未收到任何消息"
    assert received_msg.get("type") == "p2p_message", "❌ 消息类型不正确"
    assert received_msg.get("sender_username") == user_a_name, "❌ 发送者不正确"
    assert received_msg.get("content") == test_msg_content, "❌ 消息内容不匹配"
    print("✅ 在线消息转发成功")
    await client_a.close()
    await client_b.close()

    # --- 3. 离线消息存储和推送测试 ---
    print("\n--- 测试场景2：离线消息存储与上线推送 ---")
    # A 在线，C 离线
    assert token_a is not None
    client_a = WebSocketClient(token_a, "A")
    await client_a.connect()
    await client_a.get_message() # 清理上线广播

    offline_msg_content = "C 你好，看到请回复。"
    await client_a.send_message(user_c_name, offline_msg_content)

    # 验证 A 收到 C 离线的状态回执
    status_msg = await client_a.get_message()
    assert status_msg and "离线" in status_msg.get("status", ""), "❌ A 未收到 C 的离线状态回执"
    print("✅ C 离线，消息已正确提示服务端存储")
    await client_a.close()
    
    # C 现在上线
    print("\n  C 现在上线，应立即收到离线消息...")
    assert token_c is not None
    client_c = WebSocketClient(token_c, "C")
    await client_c.connect()

    # C上线后，可能会收到多条消息（自己的上线广播、其他用户的上下线广播、离线消息）
    # 我们需要在这些消息中找到我们关心的那条离线消息
    offline_msg_received = None
    for _ in range(5): # 最多检查5条消息
        msg = await client_c.get_message(timeout=2.0)
        if msg and msg.get("type") == "offline_message":
            offline_msg_received = msg
            break # 找到后就退出循环
    
    assert offline_msg_received, "❌ C 上线后未收到任何离线消息"
    assert offline_msg_received.get("sender_username") == user_a_name, "❌ 离线消息发送者不正确"
    assert offline_msg_received.get("content") == offline_msg_content, "❌ 离线消息内容不匹配"
    print("✅ C 上线后成功收到离线消息")
    await client_c.close()
    
    print("\n🎉🎉🎉 所有WebSocket测试场景均已通过! 🎉🎉🎉")

if __name__ == "__main__":
    asyncio.run(main()) 