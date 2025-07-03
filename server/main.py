from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import asyncio
import json
from typing import List, Optional
from datetime import datetime
import base64
import os
import random
import string
from pathlib import Path
from models import *
from database import init_db, get_db
from auth import verify_token, create_access_token, hash_password, verify_password
from websocket_manager import WebSocketManager
from crypto_utils import generate_key_pair, encrypt_message, decrypt_message

app = FastAPI(title="IM Backend")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
    expose_headers=["*"]  # 暴露所有头部
)

ws_manager = WebSocketManager()

@app.on_event("startup")
async def startup_event():
    init_db()
    os.makedirs("uploads", exist_ok=True)

@app.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    private_key, public_key = generate_key_pair()
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        public_key=public_key,
        private_key=private_key
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "注册成功", "user_id": user.id}

@app.post("/login")
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    token = create_access_token(data={"sub": user.username, "user_id": user.id})
    
    user.last_login = datetime.now()
    user.is_online = True
    db.commit()
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

@app.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_data["user_id"]).first()
    if user:
        user.is_online = False
        db.commit()
    return {"message": "登出成功"}

@app.get("/profile")
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_online": user.is_online,
        "last_login": user.last_login
    }

@app.get("/search_users")
async def search_users(q: str, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    users = db.query(User).filter(
        User.username.like(f"%{q}%"),
        User.id != user_data["user_id"]
    ).limit(10).all()
    
    return [{"id": user.id, "username": user.username} for user in users]

@app.post("/send_friend_request")
async def send_friend_request(request_data: FriendRequestCreate, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    
    existing_request = db.query(FriendRequest).filter(
        FriendRequest.sender_id == user_data["user_id"],
        FriendRequest.receiver_id == request_data.receiver_id
    ).first()
    
    if existing_request:
        raise HTTPException(status_code=400, detail="好友请求已发送")
    
    existing_friend = db.query(Friendship).filter(
        ((Friendship.user_id == user_data["user_id"]) & (Friendship.friend_id == request_data.receiver_id)) |
        ((Friendship.user_id == request_data.receiver_id) & (Friendship.friend_id == user_data["user_id"]))
    ).first()
    
    if existing_friend:
        raise HTTPException(status_code=400, detail="已是好友")
    
    friend_request = FriendRequest(
        sender_id=user_data["user_id"],
        receiver_id=request_data.receiver_id,
        message=request_data.message
    )
    db.add(friend_request)
    db.commit()
    
    return {"message": "好友请求已发送"}

@app.get("/friend_requests")
async def get_friend_requests(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    requests = db.query(FriendRequest).filter(
        FriendRequest.receiver_id == user_data["user_id"],
        FriendRequest.status == "pending"
    ).all()
    
    result = []
    for req in requests:
        sender = db.query(User).filter(User.id == req.sender_id).first()
        result.append({
            "id": req.id,
            "sender": {"id": sender.id, "username": sender.username},
            "message": req.message,
            "created_at": req.created_at
        })
    
    return result

@app.post("/handle_friend_request")
async def handle_friend_request(handle_data: FriendRequestHandle, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    
    friend_request = db.query(FriendRequest).filter(
        FriendRequest.id == handle_data.request_id,
        FriendRequest.receiver_id == user_data["user_id"]
    ).first()
    
    if not friend_request:
        raise HTTPException(status_code=404, detail="好友请求不存在")
    
    friend_request.status = handle_data.action
    
    if handle_data.action == "accepted":
        friendship1 = Friendship(user_id=user_data["user_id"], friend_id=friend_request.sender_id)
        friendship2 = Friendship(user_id=friend_request.sender_id, friend_id=user_data["user_id"])
        db.add(friendship1)
        db.add(friendship2)
    
    db.commit()
    return {"message": f"好友请求已{handle_data.action}"}

@app.get("/friends")
async def get_friends(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    friendships = db.query(Friendship).filter(Friendship.user_id == user_data["user_id"]).all()
    
    friends = []
    for friendship in friendships:
        friend = db.query(User).filter(User.id == friendship.friend_id).first()
        friends.append({
            "id": friend.id,
            "username": friend.username,
            "is_online": friend.is_online,
            "last_login": friend.last_login
        })
    
    return friends

@app.get("/messages/{friend_id}")
async def get_messages(friend_id: int, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    
    messages = db.query(Message).filter(
        ((Message.sender_id == user_data["user_id"]) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == user_data["user_id"]))
    ).order_by(Message.created_at.asc()).all()
    
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "content": msg.content,
            "message_type": msg.message_type,
            "created_at": msg.created_at,
            "is_encrypted": msg.is_encrypted
        })
    
    return result

@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_data = verify_token(credentials.credentials)
    
    # 确保uploads目录存在
    os.makedirs("uploads", exist_ok=True)
    
    # 生成唯一文件名，保留原始扩展名
    file_extension = Path(file.filename).suffix if file.filename else ''
    timestamp = int(datetime.now().timestamp())
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    unique_filename = f"{user_data['user_id']}_{timestamp}_{random_str}{file_extension}"
    file_path = f"uploads/{unique_filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 返回包含原始文件名和保存文件名的响应
        return {
            "filename": file.filename,  # 原始文件名
            "saved_filename": unique_filename,  # 保存的文件名
            "path": file_path,
            "size": len(content),
            "type": file.content_type or "application/octet-stream"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
@app.post("/upload_voice")
async def upload_voice(file: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_data = verify_token(credentials.credentials)
    
    # 验证音频文件
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="只支持音频文件")
    
    # 生成唯一文件名
    timestamp = int(datetime.now().timestamp())
    unique_filename = f"voice_{user_data['user_id']}_{timestamp}.webm"
    file_path = f"uploads/{unique_filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "filename": unique_filename,
            "path": file_path,
            "size": len(content),
            "duration": 0,  # 前端计算
            "type": "voice"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音上传失败: {str(e)}")

@app.post("/upload_steganography")
async def upload_steganography(
    file: UploadFile = File(...), 
    hidden_text: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_data = verify_token(credentials.credentials)
    
    # 验证图像文件
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只支持图像文件")
    
    # 生成唯一文件名
    timestamp = int(datetime.now().timestamp())
    unique_filename = f"stego_{user_data['user_id']}_{timestamp}.png"
    file_path = f"uploads/{unique_filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "filename": unique_filename,
            "path": file_path,
            "size": len(content),
            "hidden_text": hidden_text,
            "type": "steganography"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"隐写图像上传失败: {str(e)}")

@app.get("/preview_image/{filename}")
async def preview_image(filename: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    verify_token(credentials.credentials)
    
    file_path = f"uploads/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 检查是否为图像文件
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        raise HTTPException(status_code=400, detail="不是图像文件")
    
    # 根据扩展名确定MIME类型
    ext = filename.lower().split('.')[-1]
    mime_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif', 
        'bmp': 'image/bmp'
    }
    mime_type = mime_types.get(ext, 'image/png')
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        media_type=mime_type,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )
@app.get("/download_file/{filename}")
async def download_file(filename: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    verify_token(credentials.credentials)
    
    file_path = Path("uploads") / filename
    
    if not file_path.exists():
        # 调试信息
        print(f"文件不存在: {file_path}")
        existing_files = list(Path("uploads").glob("*"))
        print(f"uploads目录文件: {[f.name for f in existing_files]}")
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    
    # 获取原始文件名（如果需要）
    original_filename = filename
    
    # 自动检测MIME类型
    import mimetypes
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(file_path),
        filename=original_filename,
        media_type=mime_type
    )
@app.get("/debug/uploads")
async def debug_uploads(credentials: HTTPAuthorizationCredentials = Depends(security)):
    verify_token(credentials.credentials)
    
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        return {"error": "uploads目录不存在"}
    
    try:
        files = []
        for file_path in uploads_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "exists": file_path.exists()
                })
        
        return {
            "uploads_dir": str(uploads_dir.absolute()),
            "files": files,
            "total_files": len(files)
        }
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await ws_manager.connect(websocket, user_id)
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_online = True
        db.commit()
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "message":
                await handle_message(message_data, user_id, db)
            elif message_data["type"] == "typing":
                await handle_typing(message_data, user_id)
            elif message_data["type"] == "file":
                await handle_file_message(message_data, user_id, db)
            elif message_data["type"] == "voice":
                await handle_voice_message(message_data, user_id, db)
            elif message_data["type"] == "steganography":
                await handle_steganography_message(message_data, user_id, db)
                
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
        if user:
            user.is_online = False
            db.commit()

async def handle_message(message_data: dict, sender_id: int, db: Session):
    receiver_id = message_data["receiver_id"]
    content = message_data["content"]
    is_encrypted = message_data.get("is_encrypted", False)
    
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        message_type="text",
        is_encrypted=is_encrypted
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    response_data = {
        "type": "message",
        "id": message.id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": content,
        "message_type": "text",
        "created_at": message.created_at.isoformat(),
        "is_encrypted": is_encrypted
    }
    
    await ws_manager.send_to_user(receiver_id, json.dumps(response_data))
    await ws_manager.send_to_user(sender_id, json.dumps(response_data))

async def handle_typing(message_data: dict, sender_id: int):
    receiver_id = message_data["receiver_id"]
    is_typing = message_data["is_typing"]
    
    response_data = {
        "type": "typing",
        "sender_id": sender_id,
        "is_typing": is_typing
    }
    
    await ws_manager.send_to_user(receiver_id, json.dumps(response_data))

async def handle_file_message(message_data: dict, sender_id: int, db: Session):
    receiver_id = message_data["receiver_id"]
    file_path = message_data["file_path"]
    filename = message_data["filename"]
    saved_filename = message_data.get("saved_filename", file_path.split('/')[-1])
    
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=json.dumps({
            "file_path": file_path, 
            "filename": filename,
            "saved_filename": saved_filename
        }),
        message_type="file",
        is_encrypted=False
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    response_data = {
        "type": "file",
        "id": message.id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": message.content,
        "message_type": "file",
        "created_at": message.created_at.isoformat()
    }
    
    await ws_manager.send_to_user(receiver_id, json.dumps(response_data))
    await ws_manager.send_to_user(sender_id, json.dumps(response_data))
async def handle_voice_message(message_data: dict, sender_id: int, db: Session):
    receiver_id = message_data["receiver_id"]
    file_path = message_data["file_path"]
    filename = message_data["filename"]
    
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=json.dumps({"file_path": file_path, "filename": filename}),
        message_type="voice",
        is_encrypted=False
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    response_data = {
        "type": "voice",
        "id": message.id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": message.content,
        "message_type": "voice",
        "created_at": message.created_at.isoformat()
    }
    
    await ws_manager.send_to_user(receiver_id, json.dumps(response_data))
    await ws_manager.send_to_user(sender_id, json.dumps(response_data))

async def handle_steganography_message(message_data: dict, sender_id: int, db: Session):
    receiver_id = message_data["receiver_id"]
    file_path = message_data["file_path"]
    filename = message_data["filename"]
    
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=json.dumps({"file_path": file_path, "filename": filename}),
        message_type="steganography",
        is_encrypted=False
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    response_data = {
        "type": "steganography",
        "id": message.id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": message.content,
        "message_type": "steganography",
        "created_at": message.created_at.isoformat()
    }
    
    await ws_manager.send_to_user(receiver_id, json.dumps(response_data))
    await ws_manager.send_to_user(sender_id, json.dumps(response_data))

@app.get("/user_public_key/{user_id}")
async def get_user_public_key(user_id: int, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    verify_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"public_key": user.public_key}

@app.post("/update_p2p_info")
async def update_p2p_info(p2p_data: P2PInfoUpdate, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    existing_p2p = db.query(P2PInfo).filter(P2PInfo.user_id == user_data["user_id"]).first()
    if existing_p2p:
        existing_p2p.peer_id = p2p_data.peer_id
        existing_p2p.ip_address = p2p_data.ip_address
        existing_p2p.port = p2p_data.port
        existing_p2p.updated_at = datetime.now()
    else:
        p2p_info = P2PInfo(
            user_id=user_data["user_id"],
            peer_id=p2p_data.peer_id,
            ip_address=p2p_data.ip_address,
            port=p2p_data.port
        )
        db.add(p2p_info)
    
    db.commit()
    return {"message": "P2P信息更新成功"}

@app.get("/get_friend_p2p_info/{friend_id}")
async def get_friend_p2p_info(friend_id: int, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    
    friendship = db.query(Friendship).filter(
        Friendship.user_id == user_data["user_id"],
        Friendship.friend_id == friend_id
    ).first()
    
    if not friendship:
        raise HTTPException(status_code=404, detail="非好友关系")
    
    p2p_info = db.query(P2PInfo).filter(P2PInfo.user_id == friend_id).first()
    if not p2p_info:
        return {"p2p_available": False}
    
    return {
        "p2p_available": True,
        "peer_id": p2p_info.peer_id,
        "ip_address": p2p_info.ip_address,
        "port": p2p_info.port
    }

@app.post("/save_p2p_message")
async def save_p2p_message(message_data: P2PMessageSave, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    
    message = Message(
        sender_id=message_data.sender_id,
        receiver_id=message_data.receiver_id,
        content=message_data.content,
        message_type=message_data.message_type,
        is_encrypted=message_data.is_encrypted,
        is_p2p=True
    )
    db.add(message)
    db.commit()
    
    return {"message": "P2P消息保存成功"}

@app.delete("/remove_friend/{friend_id}")
async def remove_friend(friend_id: int, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    
    # 查找好友关系
    friendship1 = db.query(Friendship).filter(
        Friendship.user_id == user_data["user_id"],
        Friendship.friend_id == friend_id
    ).first()
    
    friendship2 = db.query(Friendship).filter(
        Friendship.user_id == friend_id,
        Friendship.friend_id == user_data["user_id"]
    ).first()
    
    if not friendship1 and not friendship2:
        raise HTTPException(status_code=404, detail="好友关系不存在")
    
    # 删除双向好友关系
    if friendship1:
        db.delete(friendship1)
    if friendship2:
        db.delete(friendship2)
    
    db.commit()
    
    return {"message": "好友已删除"}
async def get_online_friends(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_data = verify_token(credentials.credentials)
    
    friends = db.query(User).join(
        Friendship, User.id == Friendship.friend_id
    ).filter(
        Friendship.user_id == user_data["user_id"],
        User.is_online == True
    ).all()
    
    result = []
    for friend in friends:
        p2p_info = db.query(P2PInfo).filter(P2PInfo.user_id == friend.id).first()
        result.append({
            "id": friend.id,
            "username": friend.username,
            "is_online": friend.is_online,
            "p2p_available": bool(p2p_info),
            "peer_id": p2p_info.peer_id if p2p_info else None
        })
    
    return result

if __name__ == "__main__":
    import socket
    
    # 获取本机IP地址
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    local_ip = get_local_ip()
    
    print(f"🚀 服务器启动中...")
    print(f"📡 本地访问: http://localhost:8000")
    print(f"🌐 局域网访问: http://{local_ip}:8000")
    print(f"📚 API文档: http://{local_ip}:8000/docs")
    print(f"🔗 WebSocket: ws://{local_ip}:8000/ws/{{user_id}}")
    print(f"🛑 按 Ctrl+C 停止服务器")
    
    uvicorn.run(
        app, 
        host="0.0.0.0",  # 绑定所有网络接口
        port=8000,
        log_level="info",
        access_log=True
    )

