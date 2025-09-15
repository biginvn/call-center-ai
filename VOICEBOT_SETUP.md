# 🤖 VoiceBot Service Setup Guide

## 📋 Tổng quan

VoiceBot Service cho phép gọi AI voicebot thông qua extension riêng, tương tự như gọi cho agent thật. Service sử dụng OpenAI Realtime API để xử lý cuộc hội thoại real-time.

## 🔧 Cấu hình Asterisk

### 1. Thêm vào `pjsip.conf`

```ini
;=== voicebot ===
[voicebot]
type=aor
max_contacts=5
remove_existing=yes
qualify_frequency=30

[voicebot]
type=auth
auth_type=userpass
username=voicebot
password=1234

[voicebot]
type=endpoint
aors=voicebot
auth=voicebot
context=internal
dtls_auto_generate_cert=yes
webrtc=yes
disallow=all
allow=opus,ulaw
transport=transport-wss
```

### 2. Thêm vào `extensions.conf`

```ini
; Trong context [internal]
exten => 1000,1,NoOp(Incoming call to voicebot)
 same => n,Stasis(nixxis,"voicebot")
 same => n,Hangup()

exten => voicebot,1,NoOp(Incoming call to voicebot)
 same => n,Stasis(nixxis,"voicebot")
 same => n,Hangup()
```

### 3. Cấu hình `ari.conf`

```ini
[thanh]
type = user
read_only = no
password = 1234
```

## 🚀 Cách sử dụng

### 1. Gọi VoiceBot từ Browser

- **Extension**: `1000` hoặc `voicebot`
- **Context**: `internal`
- **Protocol**: WebRTC (qua browser)

### 2. Gọi VoiceBot từ SIP Client

- **Username**: `voicebot`
- **Password**: `1234`
- **Server**: IP của Asterisk server
- **Extension**: `1000`

### 3. Test VoiceBot

```bash
# Test API endpoint
curl -X GET "http://localhost:8000/voicebot/status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test VoiceBot service
curl -X POST "http://localhost:8000/voicebot/test" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔄 Luồng hoạt động

1. **Cuộc gọi đến**: User gọi extension `1000` hoặc `voicebot`
2. **StasisStart**: Asterisk chuyển cuộc gọi vào Stasis application `nixxis`
3. **VoiceBot Detection**: System phát hiện đây là voicebot call
4. **Originate**: Tạo channel mới cho voicebot
5. **OpenAI Session**: Tạo session với OpenAI Realtime API
6. **WebSocket Connection**: Kết nối WebSocket với OpenAI
7. **Audio Processing**: Xử lý audio real-time
8. **Bridge**: Kết nối caller với voicebot
9. **Conversation**: AI trò chuyện với user
10. **Hangup**: Kết thúc cuộc gọi và dọn dẹp

## 🛠️ API Endpoints

### GET `/voicebot/status`
Lấy trạng thái VoiceBot service

**Response:**
```json
{
  "status": "active",
  "active_sessions": 2,
  "voicebot_extension": "voicebot",
  "message": "VoiceBot service is running"
}
```

### POST `/voicebot/test`
Test VoiceBot service

**Response:**
```json
{
  "status": "success",
  "message": "VoiceBot service test passed",
  "openai_session_id": "sess_abc123"
}
```

### GET `/voicebot/extensions`
Lấy danh sách extensions VoiceBot

**Response:**
```json
{
  "voicebot_extensions": [
    {
      "extension": "voicebot",
      "number": "1000",
      "description": "VoiceBot extension for AI calls"
    }
  ],
  "usage": "Gọi extension 1000 hoặc 'voicebot' để kết nối với AI VoiceBot"
}
```

## 🔧 Troubleshooting

### 1. VoiceBot không trả lời
- Kiểm tra OpenAI API key
- Kiểm tra kết nối Internet
- Xem logs trong console

### 2. Audio không rõ
- Kiểm tra codec configuration
- Đảm bảo WebRTC transport hoạt động
- Kiểm tra network quality

### 3. Extension không hoạt động
- Kiểm tra cấu hình PJSIP
- Reload Asterisk configuration
- Kiểm tra dialplan context

## 📝 Logs

VoiceBot logs được ghi trong:
- **Application logs**: Console output
- **Asterisk logs**: `/var/log/asterisk/full`
- **OpenAI logs**: WebSocket connection logs

## 🔐 Security

- VoiceBot sử dụng authentication qua ARI
- OpenAI API key được bảo mật trong environment variables
- WebRTC connections sử dụng DTLS/SRTP

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Asterisk configuration
2. OpenAI API key
3. Network connectivity
4. Application logs
