#!/bin/bash

# Script setup Asterisk cho VoiceBot
# Chạy script này với quyền root hoặc sudo

echo "🚀 Bắt đầu setup Asterisk cho VoiceBot..."

# Kiểm tra quyền root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Vui lòng chạy script này với quyền root hoặc sudo"
    exit 1
fi

# Backup các file cấu hình hiện tại
echo "📁 Backup các file cấu hình hiện tại..."
cp /etc/asterisk/pjsip.conf /etc/asterisk/pjsip.conf.backup.$(date +%Y%m%d_%H%M%S)
cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.backup.$(date +%Y%m%d_%H%M%S)
cp /etc/asterisk/ari.conf /etc/asterisk/ari.conf.backup.$(date +%Y%m%d_%H%M%S)

# Cập nhật pjsip.conf
echo "📝 Cập nhật pjsip.conf..."
cat >> /etc/asterisk/pjsip.conf << 'EOF'

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
EOF

# Cập nhật extensions.conf
echo "📝 Cập nhật extensions.conf..."
cat >> /etc/asterisk/extensions.conf << 'EOF'

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
EOF

# Cập nhật ari.conf
echo "📝 Cập nhật ari.conf..."
cat >> /etc/asterisk/ari.conf << 'EOF'

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
EOF

# Tạo thư mục keys nếu chưa có
echo "🔑 Tạo SSL certificates..."
mkdir -p /etc/asterisk/keys

# Tạo self-signed certificate nếu chưa có
if [ ! -f /etc/asterisk/keys/asterisk.pem ]; then
    openssl req -new -x509 -days 365 -nodes -out /etc/asterisk/keys/asterisk.pem -keyout /etc/asterisk/keys/asterisk.key -subj "/C=VN/ST=HCM/L=HCM/O=VoiceBot/CN=asterisk"
    chmod 600 /etc/asterisk/keys/asterisk.key
    chmod 644 /etc/asterisk/keys/asterisk.pem
    chown asterisk:asterisk /etc/asterisk/keys/asterisk.*
fi

# Reload Asterisk configuration
echo "🔄 Reload Asterisk configuration..."
asterisk -rx "module reload"

# Kiểm tra trạng thái
echo "✅ Kiểm tra trạng thái Asterisk..."
asterisk -rx "core show version"
asterisk -rx "pjsip show endpoints"
asterisk -rx "ari show applications"

echo "🎉 Setup hoàn tất!"
echo ""
echo "📋 Các bước tiếp theo:"
echo "1. Kiểm tra logs: tail -f /var/log/asterisk/full"
echo "2. Test extension: asterisk -rx 'dialplan show 1000@internal'"
echo "3. Khởi động VoiceBot service"
echo "4. Gọi extension 1000 để test"
echo ""
echo "🔧 Troubleshooting:"
echo "- Kiểm tra firewall: ufw allow 5060,8088,8089"
echo "- Kiểm tra logs: /var/log/asterisk/full"
echo "- Test ARI: curl http://localhost:8088/ari/applications"
