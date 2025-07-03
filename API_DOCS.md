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

## 2. 用户搜索

### 2.1 按用户名搜索用户

根据用户名关键词模糊搜索用户，用于实现"添加好友"等功能。

- **URL**: `/users/search/{query}`
- **Method**: `GET`
- **Auth**: `Bearer Token`
- **URL Parameters**:
  - `query`: 搜索的用户名关键词。
- **Success Response**: 返回一个包含用户公开信息的对象列表。
  ```json
  [
    {
      "id": 123,
      "username": "testuser_abc",
      "is_online": true
    },
    {
      "id": 124,
      "username": "testuser_xyz",
      "is_online": false
    }
  ]
  ```

---

## 3. 联系人 (Contacts)

**认证**: 以下接口均需要 `Bearer Token`。

### 3.1 添加联系人

- **URL** : `/me/contacts/`
- **Method** : `POST`
- **Request Body**: `{"friend_id": integer}`
> 注意：这里的 `friend_id` 需要通过"按用户名搜索用户"接口获取。

### 3.2 获取联系人列表

- **URL** : `/me/contacts/`
- **Method** : `GET`
- **Success Response**: 返回一个用户对象列表，其中包含好友的详细信息，如 `id`, `username`, `is_online` 等。

### 3.3 获取在线好友列表 (高效)

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

## 4. P2P 协调与消息

### 4.1 获取用户连接信息 (P2P 关键)

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

### 4.2 WebSocket 消息系统 (核心)

WebSocket 是本系统的核心，负责在线用户的实时消息转发和离线用户的消息存储与推送。

- **URL** : `ws://127.0.0.1:8000/ws`
- **认证方式**:
  - 必须在 URL 的查询参数中提供从 `/token` 接口获取的 JWT。
  - 格式: `ws://127.0.0.1:8000/ws?token=<your_jwt_token>`

#### 4.2.1 连接与系统消息

- **连接建立**: 客户端使用带 token 的 URL 连接后，即被视为上线。
- **系统广播**: 服务器会向所有在线用户广播系统消息，通知有新用户上线或有用户下线。客户端可以监听这些消息来更新好友列表的在线状态。
  - **消息格式**: 纯文本字符串，例如 `系统消息: 用户 a 已上线。` 或 `系统消息: 用户 b 已下线。`

#### 4.2.2 客户端发送消息

- **格式**: 客户端必须发送 **JSON 格式**的字符串。
- **结构**:
  ```json
  {
    "recipient_username": "string",
    "content": "string"
  }
  ```
- **字段说明**:
  - `recipient_username`: 消息接收方的用户名。
  - `content`: 消息内容。对于加密聊天，这里应该是**加密后**的文本。

#### 4.2.3 服务器处理逻辑

- 服务器收到消息后，会进行如下处理：
  1.  根据 `recipient_username` 查找目标用户。
  2.  **如果目标用户在线** (有活跃的 WebSocket 连接)，服务器会将消息**直接转发**给该用户。
  3.  **如果目标用户不在线**，服务器会将消息作为**离线消息**存入数据库，并向发送方返回一条状态通知。

#### 4.2.4 客户端接收消息

客户端可能会收到 **4** 种类型的 JSON 消息：

1.  **在线实时消息 (P2P Message)**:
    ```json
    {
      "type": "p2p_message",
      "sender_username": "string",
      "content": "string (encrypted_content)",
      "timestamp": "string (ISO 8601 format)"
    }
    ```

2.  **离线消息 (Offline Message)**: 在客户端连接成功后，由服务器主动推送。
    ```json
    {
      "type": "offline_message",
      "sender_username": "string",
      "content": "string (encrypted_content)",
      "timestamp": "string (ISO 8601 format)"
    }
    ```
3.  **状态回执 (Status)**: 当你向一个离线用户发消息时，服务器会返回这个。
    ```json
    {
      "status": "用户 a 当前离线，消息已保存。"
    }
    ```
4.  **错误通知 (Error)**: 当发送的消息格式不正确或用户不存在时。
    ```json
    {
      "error": "错误描述文本"
    }
    ```

### 4.3 REST API (已废弃)

- **注意**: `POST /messages/` 和 `GET /messages/` 接口的功能已被整合进 WebSocket 的工作流中，**不再推荐使用**。
  - **发送**: 通过 WebSocket 发送消息给离线用户时，服务器会自动处理。
  - **接收**: 连接 WebSocket 时，服务器会自动推送。

---
*文档更新完毕。*