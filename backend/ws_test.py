import asyncio
import websockets
import requests
import json
import time

BASE_URL_HTTP = "http://127.0.0.1:8000"
BASE_URL_WS = "ws://127.0.0.1:8000"

# --- 从 api_test.py 借用的辅助函数 ---
def register_user(username, email, password):
    url = f"{BASE_URL_HTTP}/users/"
    user_data = {
        "username": username, "email": email, "password": password,
        "public_key": f"key_for_{username}"
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(user_data), headers=headers)
    return response

def login_user(username, password):
    url = f"{BASE_URL_HTTP}/token"
    login_data = {"username": username, "password": password}
    response = requests.post(url, data=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

async def ws_client(token: str, message_to_send: str, role: str = 'sender'):
    """
    一个WebSocket客户端。
    - 'sender': 连接，发送消息，然后等待接收广播。
    - 'listener': 连接，只等待接收广播。
    """
    uri = f"{BASE_URL_WS}/ws?token={token}"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"  [客户端 - {role}] WebSocket 连接成功 (token: ...{token[-6:]})")

            if role == 'sender':
                # 发送者先发送消息
                await websocket.send(message_to_send)
                print(f"  [客户端 - {role}] 已发送消息: '{message_to_send}'")

            # 两个角色都在等待接收广播
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                print(f"  [客户端 - {role}] 收到响应: '{response}'")
                return response
            except asyncio.TimeoutError:
                print(f"  [客户端 - {role}] 错误: 等待响应超时。")
                return None
    except websockets.exceptions.ConnectionClosed as e:
        print(f"  [客户端 - {role}] 错误: WebSocket 连接被关闭。代码: {e.code}, 原因: {e.reason}")
        return None

async def listen(websocket, queue: asyncio.Queue):
    """监听来自服务器的消息，并将其放入队列。"""
    try:
        while True:
            message = await websocket.recv()
            print(f"  [客户端 - listener] 收到响应: '{message}'")
            await queue.put(message)
    except websockets.exceptions.ConnectionClosed:
        print("  [客户端 - listener] 连接已关闭。")

async def main():
    # --- 准备工作：注册和登录用户 ---
    user1_name = f"ws_user1_{int(time.time())}"
    user2_name = f"ws_user2_{int(time.time())}"
    password = "ws_password"

    print("--- 1. 注册和登录用户 ---")
    # 注册用户1
    register_user(user1_name, f"{user1_name}@example.com", password)
    token1 = login_user(user1_name, password)
    assert token1, f"获取 {user1_name} 的 token 失败"
    print(f"✅ {user1_name} 登录成功。")

    # 注册用户2
    register_user(user2_name, f"{user2_name}@example.com", password)
    token2 = login_user(user2_name, password)
    assert token2, f"获取 {user2_name} 的 token 失败"
    print(f"✅ {user2_name} 登录成功。\n")

    # --- 测试核心逻辑 ---
    print("\n--- 2. WebSocket 广播测试 ---")
    listener_token = token1
    sender_token = token2
    
    listener_queue = asyncio.Queue()

    async with websockets.connect(f"{BASE_URL_WS}/ws?token={listener_token}") as listener_ws:
        print(f"  [客户端 - listener] WebSocket 连接成功 (token: ...{listener_token[-6:]})")
        
        # 启动监听者任务
        listener_task = asyncio.create_task(listen(listener_ws, listener_queue))

        # 等待一小会儿，确保监听者完全准备好
        await asyncio.sleep(0.5)

        async with websockets.connect(f"{BASE_URL_WS}/ws?token={sender_token}") as sender_ws:
            print(f"  [客户端 - sender] WebSocket 连接成功 (token: ...{sender_token[-6:]})")

            # 1. 验证发送者加入的广播
            print("  [测试] 等待发送者加入的广播消息...")
            join_message = await listener_queue.get()
            expected_join_message = f"用户 {user2_name} 加入了聊天"
            assert join_message == expected_join_message, f"期望 '{expected_join_message}', 但收到 '{join_message}'"
            print("  [测试] ✅ '加入'广播消息验证成功。")

            # 2. 发送者发送消息并验证广播
            message_to_send = "你好，世界！"
            print(f"  [客户端 - sender] 已发送消息: '{message_to_send}'")
            await sender_ws.send(message_to_send)
            
            print("  [测试] 等待聊天消息的广播...")
            chat_message = await listener_queue.get()
            expected_chat_message = f"{user2_name}: {message_to_send}"
            assert chat_message == expected_chat_message, f"期望 '{expected_chat_message}', 但收到 '{chat_message}'"
            print("  [测试] ✅ '聊天'广播消息验证成功。")

        # sender_ws 的 with 块结束，连接自动关闭
        print("  [客户端 - sender] 连接已关闭。")

        # 3. 验证发送者离开的广播
        print("  [测试] 等待发送者离开的广播消息...")
        left_message = await listener_queue.get()
        expected_left_message = f"用户 {user2_name} 已离开"
        assert left_message == expected_left_message, f"期望 '{expected_left_message}', 但收到 '{left_message}'"
        print("  [测试] ✅ '离开'广播消息验证成功。")

        # 清理
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            print("  [客户端 - listener] 任务已取消。")

    print("\n🎉 WebSocket 广播测试成功! 🎉")

if __name__ == "__main__":
    asyncio.run(main()) 