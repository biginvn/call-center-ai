# 📋 Hướng dẫn sử dụng Swagger UI với Bearer Token

## 🚀 Truy cập Swagger UI

1. **Mở browser** và truy cập: `http://localhost:8000/docs`
2. **Swagger UI** sẽ hiển thị với giao diện đầy đủ các API endpoints

## 🔐 Authentication với Bearer Token

### Bước 1: Login để lấy Access Token

#### 🔹 **Admin Login**

```bash
POST /login/admin
Content-Type: application/json

{
  "username": "admin",
  "password": "123456"
}
```

#### 🔹 **Agent Login**

```bash
POST /login/agent
Content-Type: application/json

{
  "username": "khoa",
  "password": "123456",
  "extension_number": "112"
}
```

**Response sẽ chứa**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "admin",
  "username": "admin"
}
```

### Bước 2: Authorize trong Swagger UI

1. **Click nút "Authorize"** ở góc phải trên cùng của Swagger UI
2. **Nhập token** vào field "Value":
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   📝 **Lưu ý**: Phải có prefix `Bearer ` trước token
3. **Click "Authorize"** để xác nhận
4. **Click "Close"** để đóng dialog

### Bước 3: Test APIs

Sau khi authorize thành công:

- ✅ Tất cả APIs có **lock icon** sẽ tự động include Bearer token
- ✅ Bạn có thể test trực tiếp mà không cần nhập token manually

## 📊 Các API Endpoints quan trọng

### 🏢 **Client Management APIs** (Admin only)

| Method | Endpoint        | Description         |
| ------ | --------------- | ------------------- |
| GET    | `/clients/`     | Lấy tất cả clients  |
| POST   | `/clients/`     | Tạo client mới      |
| GET    | `/clients/{id}` | Lấy chi tiết client |
| PUT    | `/clients/{id}` | Cập nhật client     |
| DELETE | `/clients/{id}` | Xóa client          |

### 🤖 **AI Management APIs**

| Method | Endpoint               | Description           |
| ------ | ---------------------- | --------------------- |
| GET    | `/ai/instructions`     | Lấy AI configuration  |
| POST   | `/ai/instructions`     | Tạo AI config mới     |
| PUT    | `/ai/instructions`     | Cập nhật AI config    |
| GET    | `/ai/instructions/all` | Lấy tất cả AI configs |

### 👥 **User Management APIs**

| Method | Endpoint       | Description                 |
| ------ | -------------- | --------------------------- |
| GET    | `/user/all`    | Lấy tất cả users            |
| GET    | `/user/`       | Lấy thông tin user hiện tại |
| GET    | `/user/active` | Lấy active users            |

### 💬 **Conversation APIs**

| Method | Endpoint              | Description                 |
| ------ | --------------------- | --------------------------- |
| GET    | `/conversations/`     | Lấy danh sách conversations |
| GET    | `/conversations/{id}` | Lấy chi tiết conversation   |

## 🔧 Example Test Scenarios

### Scenario 1: Admin tạo Client mới

1. **Login admin** → Copy access_token
2. **Authorize** trong Swagger UI
3. **Test POST `/clients/`** với payload:
   ```json
   {
     "name": "Công ty ABC",
     "description": "Client cho công ty ABC"
   }
   ```

### Scenario 2: Cập nhật AI Instructions

1. **Login** (admin hoặc agent)
2. **Authorize** trong Swagger UI
3. **Test PUT `/ai/instructions`** với payload:
   ```json
   {
     "instructions": "Bạn là tổng đài viên chuyên nghiệp...",
     "voice": "shimmer"
   }
   ```

## 🚨 Troubleshooting

### ❌ **401 Unauthorized**

- Kiểm tra token có đúng format `Bearer <token>` không
- Token có thể đã hết hạn → Login lại để lấy token mới

### ❌ **403 Forbidden**

- User không đủ quyền truy cập endpoint
- Admin có full quyền, Agent có quyền hạn chế

### ❌ **Internal Server Error**

- Kiểm tra server logs
- Có thể do lỗi client_id fields (đã tạm thời disable)

## 💡 Tips và Best Practices

1. **Token expiry**: Access token có thời hạn, cần login lại khi hết hạn
2. **Persistent auth**: Swagger UI sẽ nhớ token trong session
3. **Multiple roles**: Test với cả admin và agent để thấy sự khác biệt về permissions
4. **Error handling**: Đọc error response để hiểu lỗi và cách fix

## 🎯 Next Steps

Sau khi test thành công với Swagger UI:

1. **Integrate với Frontend**: Sử dụng token trong React/Vue.js app
2. **Mobile testing**: Test với Postman hoặc mobile apps
3. **Load testing**: Test performance với nhiều concurrent requests

---

**🚀 Happy Testing!** Nếu có vấn đề gì, check server logs hoặc liên hệ dev team.
