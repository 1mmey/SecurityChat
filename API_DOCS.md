# 安全即时通讯系统 - 后端 API 文档

本文档为前端开发人员提供了与后端服务进行交互所需的全部 API 接口信息。

## 0. 基础信息

- **后端服务根地址**: `http://127.0.0.1:8000`
- **自动交互式文档 (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **认证方式**: 大部分接口使用 `Bearer Token` 进行认证。在登录后，将获取到的 `access_token` 放入请求头的 `Authorization` 字段中，格式为 `Bearer <your_jwt_token>`。

---

## 1. 认证 (Authentication)

### 1.1 用户注册

创建一个新用户。

- **URL** : `/users/`
- **Method** : `POST`
- **Request Body**:
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "public_key": "string" 
}
```
> `public_key` 是用户的加密公钥，用于端到端加密。

### 1.2 用户登录 (获取 Token)

使用用户名和密码登录，获取用于认证的 JWT。登录成功后，服务器会记录该用户的在线状态和IP地址。

- **URL** : `/token`
- **Method** : `POST`
- **Request Body** (form-data): `username` 和 `password`

### 1.3 用户登出

主动通知服务器用户下线。

- **URL** : `/logout`
- **Method** : `POST`
- **Auth**: `Bearer Token`
- **Success Response**: `200 OK` with `{"detail": "Logged out successfully"}`

---

## 2. 联系人 (Contacts)

**认证**: 以下接口均需要 `Bearer Token`。

### 2.1 添加联系人

- **URL** : `/me/contacts/`
- **Method** : `POST`
- **Request Body**: `{"friend_username": "string"}`

### 2.2 获取联系人列表

- **URL** : `/me/contacts/`
- **Method** : `GET`
- **Success Response**: 返回一个用户对象列表，其中包含好友的详细信息，如 `id`, `username`, `is_online` 等。

### 2.3 获取在线好友列表 (高效)

高效地一次性获取所有在线好友的连接信息列表，用于构建好友在线状态面板。

- **URL** : `/me/contacts/online`
- **Method** : `GET`
- **Auth**: `Bearer Token`
- **Success Response**: 返回一个包含所有在线好友连接信息的对象列表。
  ```json
  [
    {
      "username": "user2_example",
      "public_key": "key_for_user2_example",
      "ip_address": "127.0.0.1",
      "port": 6953
    }
  ]
  ```

---

## 3. P2P 协调与消息

### 3.1 获取用户连接信息 (P2P 关键)

获取指定用户的连接信息，用于尝试建立 P2P 直连。

- **URL** : `/users/{username}/connection-info`
- **Method** : `GET`
- **Auth**: `Bearer Token`
- **Success Response**:
```json
{
  "public_key": "string",
  "ip_address": "string",
  "port": integer
}
```
- **Error Response**:
  - `404 Not Found`: 如果用户不存在或**不在线**。

### 3.2 WebSocket 消息中继 (P2P Fallback)

当 P2P 直连失败时，使用此 WebSocket 作为备用方案进行实时消息转发。

- **URL** : `ws://127.0.0.1:8000/ws`
- **连接方式**:
  - 必须在 URL 的查询参数中提供 Token 进行认证。
  - 格式: `ws://127.0.0.1:8000/ws?token=<your_jwt_token>`
- **行为**:
  - 连接成功后，客户端会收到其他用户加入/离开的广播。
  - 客户端可以向服务器发送文本消息，服务器会将其广播给**所有其他**在线的用户。
  - 消息格式: `"{发送者用户名}: {消息内容}"`

### 3.3 发送离线消息

当检测到目标用户不在线时，客户端可调用此接口，将加密后的消息交由服务器存储。

- **URL** : `/messages/`
- **Method** : `POST`
- **Auth**: `Bearer Token`
- **Request Body**:
```json
{
  "recipient_username": "string",
  "encrypted_content": "string (base64 encoded)"
}
```
- **Success Response**: 返回创建的消息对象。

### 3.4 获取离线消息

客户端登录后，应调用此接口拉取所有发给自己的离线消息。

- **URL** : `/messages/`
- **Method** : `GET`
- **Auth**: `Bearer Token`
- **Success Response**:
  - 返回一个消息对象列表。
  - **重要**: 此接口会自动将返回的消息在数据库中标记为"已读"。客户端再次调用将不会重复获取到相同的消息。
```json
[
  {
    "id": 1,
    "sender_id": 15,
    "receiver_id": 14,
    "encrypted_content": "SGVsbG8gd29ybGQh",
    "sent_at": "2025-07-01T10:00:02"
  }
]
```

---
*后续接口（如消息收发等）将在此处继续更新。*