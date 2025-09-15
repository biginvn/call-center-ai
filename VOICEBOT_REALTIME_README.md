# ChatGPT VoiceBot với OpenAI Realtime API

## Tổng quan

VoiceBot này sử dụng OpenAI Realtime API để tạo ra trải nghiệm hội thoại speech-to-speech realtime với độ trễ thấp. Thay vì sử dụng Whisper + TTS riêng biệt, hệ thống sử dụng OpenAI Realtime API để xử lý toàn bộ pipeline từ giọng nói đến giọng nói.

## Kiến trúc

```
Asterisk ARI ←→ FastAPI Application ←→ OpenAI Realtime API
     ↓                    ↓                      ↓
  Cuộc gọi          Audio Stream          Speech-to-Speech
```

## Tính năng chính

- **Speech-to-Speech Realtime**: Xử lý giọng nói realtime với độ trễ thấp
- **Tích hợp Asterisk ARI**: Kết nối trực tiếp với Asterisk thông qua ARI
- **Audio Streaming**: Stream audio trực tiếp giữa Asterisk và OpenAI
- **Multi-call Support**: Hỗ trợ nhiều cuộc gọi đồng thời
- **Health Monitoring**: API endpoints để kiểm tra trạng thái

## Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình environment variables

Copy file `env.example` thành `.env` và cập nhật các giá trị:

```bash
cp env.example .env
```

Các biến quan trọng:
- `OPENAI_API_KEY`: API key của OpenAI
- `ARI_HOST`, `ARI_PORT`, `ARI_USERNAME`, `ARI_PASSWORD`: Cấu hình Asterisk ARI
- `ARI_APP_NAME`: Tên ứng dụng ARI (phải khớp với cấu hình Asterisk)

### 3. Cấu hình Asterisk

Đảm bảo Asterisk được cấu hình để:
- ARI được bật
- Extension 1000 được cấu hình để chuyển cuộc gọi vào Stasis app
- WebSocket được bật cho ARI

## Sử dụng

### 1. Khởi động ứng dụng

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Kiểm tra trạng thái

```bash
# Kiểm tra trạng thái VoiceBot
curl http://localhost:8000/voicebot/status

# Kiểm tra sức khỏe
curl http://localhost:8000/voicebot/health
```

### 3. Gọi điện

Gọi tới extension 1000 để bắt đầu hội thoại với VoiceBot.

## API Endpoints

### VoiceBot Status
- `GET /voicebot/status` - Lấy trạng thái VoiceBot
- `GET /voicebot/health` - Kiểm tra sức khỏe VoiceBot

### Response mẫu

```json
{
  "status": "success",
  "data": {
    "is_connected": true,
    "active_calls": 2,
    "total_calls_today": 15,
    "uptime": "2h 30m 45s",
    "version": "1.0.0",
    "last_error": null
  }
}
```

## Cấu trúc Code

### Services

- `VoiceBotService`: Service chính quản lý toàn bộ VoiceBot
- `ARIClient`: Client kết nối với Asterisk ARI
- `OpenAIRealtimeService`: Service xử lý OpenAI Realtime API
- `AudioStreamHandler`: Handler xử lý audio streaming
- `CallHandler`: Handler xử lý các sự kiện cuộc gọi

### Models

- `CallSession`: Model cho session cuộc gọi
- `VoiceBotStatus`: Model cho trạng thái VoiceBot
- `ARIEvent`: Model cho ARI events

## Luồng hoạt động

1. **Cuộc gọi đến**: Asterisk chuyển cuộc gọi vào Stasis app
2. **Khởi tạo session**: Tạo OpenAI Realtime session
3. **Audio streaming**: Bắt đầu stream audio giữa Asterisk và OpenAI
4. **Hội thoại**: Xử lý hội thoại realtime
5. **Kết thúc**: Dọn dẹp tài nguyên khi cuộc gọi kết thúc

## Troubleshooting

### Lỗi kết nối ARI
- Kiểm tra cấu hình Asterisk ARI
- Đảm bảo username/password đúng
- Kiểm tra firewall và network

### Lỗi OpenAI API
- Kiểm tra API key
- Đảm bảo có quyền truy cập Realtime API
- Kiểm tra rate limits

### Lỗi audio streaming
- Kiểm tra cấu hình audio format
- Đảm bảo Asterisk hỗ trợ WebSocket streaming
- Kiểm tra network latency

## Monitoring

### Logs
Ứng dụng ghi log chi tiết cho:
- Kết nối ARI
- Tạo/dừng sessions
- Audio streaming
- Lỗi và exceptions

### Metrics
- Số cuộc gọi đang hoạt động
- Thời gian uptime
- Trạng thái kết nối
- Lỗi gần nhất

## Bảo mật

- Sử dụng HTTPS cho production
- Bảo vệ API keys
- Cấu hình firewall phù hợp
- Giới hạn quyền truy cập ARI

## Performance

- Hỗ trợ nhiều cuộc gọi đồng thời
- Audio streaming với độ trễ thấp
- Tự động dọn dẹp tài nguyên
- Connection pooling cho ARI

## Mở rộng

### Thêm tính năng
- Recording cuộc gọi
- Analytics và reporting
- Custom voice models
- Multi-language support

### Tích hợp
- CRM systems
- Call center software
- Monitoring tools
- Analytics platforms
