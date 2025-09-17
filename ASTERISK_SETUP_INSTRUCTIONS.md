# 🎯 Hướng dẫn Cấu hình Asterisk cho VoiceBot

## 📋 Tổng quan

Để VoiceBot hoạt động với audio, bạn cần cấu hình Asterisk đúng cách. Dưới đây là hướng dẫn từng bước.

## 🔧 Bước 1: Cấu hình PJSIP (pjsip.conf)

### 1.1 Backup file hiện tại
```bash
sudo cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.backup
```

### 1.2 Thêm cấu hình VoiceBot vào cuối file `/etc/asterisk/pjsip.conf`:

```ini
;=== VoiceBot Configuration ===
; Transport configuration
[transport-wss]
type=transport
protocol=wss
bind=0.0.0.0:8089
cert_file=/etc/asterisk/keys/asterisk.pem
priv_key_file=/etc/asterisk/keys/asterisk.key

; Transport for regular SIP
[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060

; Extension 1000 AOR
[1000]
type=aor
max_contacts=5
remove_existing=yes
qualify_frequency=30

; Extension 1000 Auth
[1000]
type=auth
auth_type=userpass
username=1000
password=1234

; Extension 1000 Endpoint
[1000]
type=endpoint
aors=1000
auth=1000
context=internal
dtls_auto_generate_cert=yes
webrtc=yes
disallow=all
allow=opus,ulaw,alaw
transport=transport-wss
direct_media=no
ice_support=yes

; VoiceBot endpoint (for internal calls)
[voicebot]
type=aor
max_contacts=1
remove_existing=yes

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
disallow=all
allow=opus,ulaw,alaw
direct_media=no
```

## 🔧 Bước 2: Cấu hình Extensions (extensions.conf)

### 2.1 Backup file hiện tại
```bash
sudo cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup
```

### 2.2 Thêm cấu hình VoiceBot vào cuối file `/etc/asterisk/extensions.conf`:

```ini
;=== VoiceBot Extensions ===
[internal]
; Voicebot extension - gọi từ browser hoặc internal
exten => 1000,1,NoOp(Incoming call to voicebot extension 1000)
 same => n,Answer()
 same => n,Wait(1)
 same => n,Stasis(nixxis,"voicebot")
 same => n,Hangup()

; Voicebot extension với alias
exten => voicebot,1,NoOp(Incoming call to voicebot alias)
 same => n,Answer()
 same => n,Wait(1)
 same => n,Stasis(nixxis,"voicebot")
 same => n,Hangup()

; Fallback cho voicebot calls
exten => _X.,1,NoOp(Incoming call to voicebot pattern)
 same => n,Answer()
 same => n,Wait(1)
 same => n,Stasis(nixxis,"voicebot")
 same => n,Hangup()

; Context cho incoming calls
[from-internal]
; Route calls to voicebot
exten => 1000,1,NoOp(Routing to voicebot)
 same => n,Dial(PJSIP/1000,30)
 same => n,Hangup()

; Context cho external calls
[from-external]
; Route external calls to voicebot
exten => 1000,1,NoOp(External call to voicebot)
 same => n,Dial(PJSIP/1000,30)
 same => n,Hangup()
```

## 🔧 Bước 3: Cấu hình ARI (ari.conf)

### 3.1 Backup file hiện tại
```bash
sudo cp /etc/asterisk/ari.conf /etc/asterisk/ari.conf.backup
```

### 3.2 Thêm cấu hình VoiceBot vào cuối file `/etc/asterisk/ari.conf`:

```ini
[general]
enabled = yes
pretty = yes
allowed_origins = http://18.143.54.64:8088,http://localhost:8088,http://127.0.0.1:8088,http://0.0.0.0:8088

[thanh]
type = user
read_only = no
password = 1234
password_format = plain

; Thêm user cho voicebot service
[voicebot_user]
type = user
read_only = no
password = 1234
password_format = plain
```

## 🔧 Bước 4: Tạo SSL Certificates

### 4.1 Tạo thư mục keys
```bash
sudo mkdir -p /etc/asterisk/keys
```

### 4.2 Tạo self-signed certificate
```bash
sudo openssl req -new -x509 -days 365 -nodes -out /etc/asterisk/keys/asterisk.pem -keyout /etc/asterisk/keys/asterisk.key -subj "/C=VN/ST=HCM/L=HCM/O=VoiceBot/CN=asterisk"
```

### 4.3 Set permissions
```bash
sudo chmod 600 /etc/asterisk/keys/asterisk.key
sudo chmod 644 /etc/asterisk/keys/asterisk.pem
sudo chown asterisk:asterisk /etc/asterisk/keys/asterisk.*
```

## 🔧 Bước 5: Cấu hình Firewall

### 5.1 Mở các ports cần thiết
```bash
# SIP port
sudo ufw allow 5060/udp

# ARI port
sudo ufw allow 8088/tcp

# WebRTC port
sudo ufw allow 8089/tcp

# RTP ports (cho audio)
sudo ufw allow 10000:20000/udp
```

## 🔧 Bước 6: Reload Asterisk Configuration

### 6.1 Reload modules
```bash
sudo asterisk -rx "module reload"
```

### 6.2 Hoặc restart Asterisk
```bash
sudo systemctl restart asterisk
```

## 🔧 Bước 7: Kiểm tra Cấu hình

### 7.1 Kiểm tra version
```bash
sudo asterisk -rx "core show version"
```

### 7.2 Kiểm tra endpoints
```bash
sudo asterisk -rx "pjsip show endpoints"
```

### 7.3 Kiểm tra dialplan
```bash
sudo asterisk -rx "dialplan show 1000@internal"
```

### 7.4 Kiểm tra ARI
```bash
curl http://localhost:8088/ari/applications
```

## 🔧 Bước 8: Test VoiceBot

### 8.1 Khởi động VoiceBot service
```bash
cd /path/to/your/voicebot
python -m app.main
```

### 8.2 Test cuộc gọi
- Gọi extension `1000` từ SIP client
- Hoặc sử dụng WebRTC trong browser
- Kiểm tra logs để xem audio flow

## 🔧 Bước 9: Troubleshooting

### 9.1 Kiểm tra logs
```bash
# Asterisk logs
sudo tail -f /var/log/asterisk/full

# VoiceBot logs
tail -f logs.txt
```

### 9.2 Kiểm tra kết nối ARI
```bash
curl -u thanh:1234 http://localhost:8088/ari/applications
```

### 9.3 Kiểm tra endpoints
```bash
sudo asterisk -rx "pjsip show endpoints"
sudo asterisk -rx "pjsip show contacts"
```

### 9.4 Test audio codecs
```bash
sudo asterisk -rx "core show codecs"
```

## 🎯 Các Lỗi Thường Gặp

### Lỗi 1: "No such context 'internal'"
**Giải pháp**: Đảm bảo context `[internal]` được định nghĩa trong `extensions.conf`

### Lỗi 2: "ARI connection failed"
**Giải pháp**: 
- Kiểm tra `ari.conf` có đúng không
- Kiểm tra firewall port 8088
- Kiểm tra username/password

### Lỗi 3: "No audio heard"
**Giải pháp**:
- Kiểm tra codec configuration
- Kiểm tra RTP ports
- Kiểm tra bridge configuration

### Lỗi 4: "WebRTC connection failed"
**Giải pháp**:
- Kiểm tra SSL certificates
- Kiểm tra port 8089
- Kiểm tra DTLS configuration

## 📞 Test Commands

### Test ARI connection
```bash
curl -u thanh:1234 http://localhost:8088/ari/applications
```

### Test extension
```bash
sudo asterisk -rx "dialplan show 1000@internal"
```

### Test PJSIP
```bash
sudo asterisk -rx "pjsip show endpoints"
sudo asterisk -rx "pjsip show contacts"
```

### Test audio
```bash
sudo asterisk -rx "core show codecs"
sudo asterisk -rx "rtp show settings"
```

## 🎉 Kết quả Mong đợi

Sau khi setup xong, bạn sẽ có:
- ✅ Extension 1000 hoạt động
- ✅ ARI connection thành công
- ✅ Audio streaming hoạt động
- ✅ VoiceBot có thể nghe và nói
- ✅ WebRTC support cho browser calls

## 📝 Lưu ý Quan trọng

1. **Backup**: Luôn backup các file cấu hình trước khi thay đổi
2. **Permissions**: Đảm bảo quyền truy cập đúng cho các file
3. **Firewall**: Mở đúng các ports cần thiết
4. **Logs**: Theo dõi logs để debug
5. **Testing**: Test từng bước một cách cẩn thận

## 🆘 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra logs: `/var/log/asterisk/full`
2. Kiểm tra cấu hình: `asterisk -rx "config show"`
3. Test từng component riêng biệt
4. Kiểm tra network connectivity
5. Xem lại các bước setup
