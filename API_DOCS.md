# 安全即时通讯系统 - 后端 API 文档

本文档旨在为前端开发人员提供与后端服务进行交互所需的 API 接口信息。

## 1. API 文档地址

后端服务启动后，会自动生成一个交互式的 API 文档页面。您可以通过下面的地址访问它，里面包含了所有可用的 API 接口、请求参数和响应格式的详细说明。

- **API 文档 (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **备用 API 文档 (ReDoc):** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

**注意：** 访问前请确保后端服务正在本地运行。

## 2. 用户 (Users)

### 2.1 用户注册

创建一个新用户。

- **URL** : `/users/`
- **Method** : `POST`
- **Request Body** :

```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "public_key": "string"
}
```

- **Success Response** :
  - **Code** : `200 OK`
  - **Content** :
    ```json
    {
      "username": "string",
      "email": "user@example.com",
      "id": 0,
      "created_at": "2025-06-30T17:35:28.123Z"
    }
    ```

- **Error Response** :
  - **Code** : `400 Bad Request`
  - **Content** :
    ```json
    { "detail": "Username already registered" }
    ```
    或者
    ```json
    { "detail": "Email already registered" }
    ```

---
*后续接口（如用户登录、联系人管理等）将在此处继续更新。*