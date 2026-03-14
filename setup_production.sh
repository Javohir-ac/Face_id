#!/bin/bash
# 🛡️ ROBUST FACE ID PRODUCTION SETUP SCRIPT

echo "🛡️  Robust Face ID Production Setup boshlandi..."

# Ranglar
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Funksiyalar
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_robust() {
    echo -e "${PURPLE}[ROBUST]${NC} $1"
}

# 1. Tizim ma'lumotlarini tekshirish
log_info "Tizim ma'lumotlarini tekshirish..."
echo "OS: $(uname -s)"
echo "Kernel: $(uname -r)"
echo "Python: $(python3 --version 2>/dev/null || echo 'Python3 topilmadi')"
echo "Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Disk: $(df -h . | awk 'NR==2 {print $4 " available"}')"

# 2. Kerakli paketlarni o'rnatish
log_info "Tizim paketlarini yangilash..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv cmake build-essential jq curl
elif command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y python3-pip python3-venv cmake gcc gcc-c++ jq curl
elif command -v pacman &> /dev/null; then
    sudo pacman -Syu --noconfirm python-pip cmake base-devel jq curl
else
    log_warning "Package manager topilmadi, manual o'rnatish kerak"
fi

# 3. Virtual environment yaratish
log_info "Virtual environment yaratish..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "Virtual environment yaratildi"
else
    log_warning "Virtual environment allaqachon mavjud"
fi

# 4. Virtual environment aktivlashtirish
log_info "Virtual environment aktivlashtirish..."
source venv/bin/activate

# 5. Dependencies o'rnatish
log_info "Python dependencies o'rnatish..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Kerakli papkalarni yaratish
log_info "Kerakli papkalarni yaratish..."
mkdir -p logs backups cache face_data state_backup

# 7. Robust recovery scriptlarini executable qilish
log_robust "Recovery scriptlarini sozlash..."
chmod +x auto_recovery.py
chmod +x robust_recovery.py

# 8. Systemd service yaratish (Robust version)
log_robust "Robust systemd service yaratish..."
CURRENT_DIR=$(pwd)
USER_NAME=$(whoami)

cat > face-id-robust.service << EOF
[Unit]
Description=Face ID Recognition System (Robust)
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python main.py
ExecStartPre=$CURRENT_DIR/venv/bin/python robust_recovery.py cleanup
ExecStopPost=$CURRENT_DIR/venv/bin/python robust_recovery.py backup
Restart=always
RestartSec=30
StartLimitBurst=5
StandardOutput=journal
StandardError=journal

# Robust settings
TimeoutStartSec=60
TimeoutStopSec=30
KillMode=mixed
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
EOF

# Service faylini ko'chirish
if [ -w "/etc/systemd/system/" ]; then
    sudo cp face-id-robust.service /etc/systemd/system/
    sudo systemctl daemon-reload
    log_success "Robust systemd service yaratildi"
else
    log_warning "Systemd service yaratish uchun sudo kerak:"
    echo "sudo cp face-id-robust.service /etc/systemd/system/"
    echo "sudo systemctl daemon-reload"
fi

echo ""
echo "🛡️  ROBUST PRODUCTION SETUP TUGALLANDI!"
echo "========================================="
echo ""
echo "🔥 PRODUCTION READY WITH ROBUST PROTECTION!"