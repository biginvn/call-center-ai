# Cấu hình Extension 1000 cho Asterisk

## 📋 Các file cấu hình cần thiết:

### 1. **pjsip_1000.conf** → `/etc/asterisk/pjsip.conf`
- Cấu hình PJSIP cho extension 1000
- Transport WebSocket Secure (WSS)
- Authentication và endpoint

### 2. **http_1000.conf** → `/etc/asterisk/http.conf`
- Cấu hình HTTP/HTTPS server
- WebSocket support
- SSL/TLS certificates

### 3. **ari_1000.conf** → `/etc/asterisk/ari.conf`
- Cấu hình ARI (Asterisk REST Interface)
- User authentication
- CORS settings

### 4. **extensions_1000.conf** → `/etc/asterisk/extensions.conf`
- Dialplan cho extension 1000
- Voicebot routing
- Stasis application

## 🔧 Cách cài đặt:

### Bước 1: Copy các file cấu hình
```bash
# Copy PJSIP config
sudo cp asterisk_configs/pjsip_1000.conf /etc/asterisk/pjsip.conf

# Copy HTTP config
sudo cp asterisk_configs/http_1000.conf /etc/asterisk/http.conf

# Copy ARI config
sudo cp asterisk_configs/ari_1000.conf /etc/asterisk/ari.conf

# Copy Extensions config
sudo cp asterisk_configs/extensions_1000.conf /etc/asterisk/extensions.conf
```

### Bước 2: Reload cấu hình
```bash
# Trong Asterisk CLI
module reload res_pjsip.so
dialplan reload
```

### Bước 3: Kiểm tra
```bash
# Kiểm tra endpoints
pjsip show endpoints

# Kiểm tra HTTP status
http show status

# Kiểm tra transports
pjsip show transports
```

## 🎯 Thông tin kết nối:

- **Server:** 18.143.54.64:8088 (HTTP) hoặc 8089 (HTTPS)
- **Username:** 1000
- **Password:** 1234
- **Transport:** WS (HTTP) hoặc WSS (HTTPS)
- **WebSocket Endpoint:** /ws

## ⚠️ Lưu ý:

1. **Certificates:** Đảm bảo có certificates trong `/etc/asterisk/keys/`
2. **Firewall:** Mở ports 8088 và 8089
3. **CORS:** Cấu hình CORS cho web client
4. **SSL:** Nếu có lỗi SSL, sử dụng HTTP (port 8088) thay vì HTTPS (port 8089)

## 🧪 Test:

1. Mở file `extension_1000_register.html` trong browser
2. Nhấn "Kết nối" để đăng ký extension 1000
3. Kiểm tra trong Asterisk CLI: `pjsip show endpoints`
