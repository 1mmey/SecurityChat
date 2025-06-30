# **安全即时通讯系统 - 5日冲刺开发计划**

本文档是项目的核心指南，请所有成员每日参照此文档进行开发。

---

### **🎯 5日冲刺目标 (MVP - 最低可行产品)**

我们的目标是在5天内，完成一个可以演示的核心功能版本。**所有任务都应围绕以下MVP展开**：

1.  **用户系统:** 用户可以成功 **注册** 和 **登录**。
2.  **好友列表:** 登录后，可以看到 **在线的好友**。
3.  **实时聊天:** 可以与在线好友进行 **1对1的实时文本聊天**。
4.  **安全性:** 聊天内容经过 **端到端加密**。

*注意：信息隐藏、语音聊天、头像等功能均为加分项，在完成MVP后若有时间再考虑。*

---

### **🛠️ 技术栈**

*   **后端:** Python, **FastAPI**, Uvicorn, `python-jose` (用于JWT认证)
*   **前端:** **uniapp** (Vue 3), **Element Plus** (仅用于H5端), Pinia
*   **实时通信:** **WebSockets** (用于信令), **WebRTC** (用于P2P数据)
*   **数据库:** SQLite

---

### **🚀 快速启动指南**

**后端:**
```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pip install -r ../requirements.txt

# 3. 启动服务器 (开发模式，自动重载)
uvicorn server:app --reload
```
> 服务器运行在 `http://127.0.0.1:8000`

**前端 (uniapp):**
```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 以H5模式启动开发服务器 (用于Web浏览器预览)
npm run dev:h5
```
> 前端开发服务器运行在 `http://localhost:5173` (或类似地址)

---

### **✅ 任务清单 (To-Do List)**

#### **后端任务 (由后端同学负责)**

- [ ] **Day 1: 基础搭建**
    - [ ] 初始化FastAPI项目。
    - [ ] 设计并创建SQLite数据库表 (`users`, `friends`)。
    - [ ] 编写Pydantic模型用于数据校验 (`UserCreate`, `UserLogin`)。

- [ ] **Day 2: 用户认证**
    - [ ] 实现用户注册API接口 (`/register`)。
    - [ ] 实现用户登录API接口 (`/login`)，成功后返回JWT Token。
    - [ ] 实现一个需要JWT认证的测试接口，以验证Token有效性。

- [ ] **Day 3: WebSocket连接管理**
    - [ ] 创建一个WebSocket端点 (`/ws/{token}`) 用于接收客户端连接。
    - [ ] 实现一个`ConnectionManager`类，用于管理所有活跃的WebSocket连接。
    - [ ] 用户通过WebSocket连接后，解析Token，标记用户为在线，并将其连接存入管理器。
    - [ ] 当用户断开连接时，将其从管理器中移除。

- [ ] **Day 4: WebRTC信令与好友逻辑**
    - [ ] 实现好友列表接口 (`/friends`)，返回当前用户的好友及其在线状态。
    - [ ] 在WebSocket中实现WebRTC信令转发逻辑 (offer, answer, ice-candidate)。
    - [ ] 实现添加好友的接口。

- [ ] **Day 5: 联调与收尾**
    - [ ] 与前端进行密集联调，修复BUG。
    - [ ] 确保所有API和WebSocket消息格式与前端约定一致。
    - [ ] 整理代码，添加必要的注释。

#### **前端任务 (uniapp - 由前端同学分工协作)**

- [ ] **Day 1: 项目搭建与登录页**
    - [ ] **安装依赖:** `npm install element-plus pinia axios`
    - [ ] **配置 `main.js`:** 引入并注册 `Pinia`。
    - [ ] **配置 `vite.config.js`:** 按需引入 `Element Plus` 以减小打包体积。
    - [ ] **页面与路由:** 在 `src/pages.json` 中配置登录页和聊天主页的路径。
    - [ ] **状态管理:** 创建Pinia store (`src/store/auth.js`) 用于管理用户Token。
    - [ ] **UI开发:** 在 `src/pages/login/login.vue` 中，使用 `Element Plus` 组件完成登录/注册页面的UI布局。

- [ ] **Day 2: 实现登录逻辑**
    - [ ] **API服务:** 在 `src/services/api.js` 中，使用 `axios` 编写调用后端注册/登录接口的函数。
    - [ ] **登录流程:** 实现完整的登录流程：调用API -> 获取Token -> 存入Pinia和`uni.setStorageSync` -> 使用 `uni.reLaunch` 跳转到聊天页。
    - [ ] **路由拦截:** 在 `src/main.js` 或单独的拦截器文件中，使用 `uni.addInterceptor` 实现路由守卫，未登录用户访问聊天页时自动跳转到登录页。

- [ ] **Day 3: 聊天主界面与WebSocket**
    - [ ] **UI开发:** 搭建聊天主界面UI (`src/pages/chat/chat.vue`)，包括好友列表和聊天窗口区域。
    - [ ] **WebSocket服务:** 封装 `uni.connectSocket`，在进入聊天页后自动连接后端WebSocket。
    - [ ] **数据渲染:** 从后端获取好友列表并渲染到界面上，区分在线状态。

- [ ] **Day 4: WebRTC实现**
    - [ ] **WebRTC服务:** 编写WebRTC处理器，封装创建连接、处理信令的逻辑。
    - [ ] **信令交互:** 实现点击好友后，通过WebSocket信令与对方建立WebRTC连接的完整流程。
    - [ ] **数据通道:** 实现通过WebRTC DataChannel发送和接收文本消息。

- [ ] **Day 5: 联调与收尾**
    - [ ] **消息显示:** 将收到的消息显示在聊天窗口中。
    - [ ] **端到端加密:** 在发送消息前加密，在收到消息后解密 (使用浏览器原生`SubtleCrypto` API)。
    - [ ] **体验优化:** 整体UI/UX优化和BUG修复。

---

### **📡 核心通信协议**

**WebSocket消息格式 (JSON):**
```json
{
  "type": "event_name",
  "payload": { ... }
}
```
**示例:**
*   **A向B发起通话请求 (A -> Server -> B):**
    `{"type": "webrtc-offer", "payload": {"sdp": ..., "target_user": "B"}}`
*   **B回应A (B -> Server -> A):**
    `{"type": "webrtc-answer", "payload": {"sdp": ..., "target_user": "A"}}`
*   **交换ICE候选 (A <-> Server <-> B):**
    `{"type": "webrtc-ice-candidate", "payload": {"candidate": ..., "target_user": "..."}}`

---


