# 🚀 FACE ID DEPLOY YECHIMLARI

## 1. SYSTEMD SERVICE (Linux uchun)

### face-id.service yaratish:
```bash
sudo nano /etc/systemd/system/face-id.service
```

```ini
[Unit]
Description=Face ID Recognition System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/your/face_id
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Service ishga tushirish:
```bash
sudo systemctl daemon-reload
sudo systemctl enable face-id.service
sudo systemctl start face-id.service
sudo systemctl status face-id.service
```

## 2. DOCKER CONTAINER

### Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "main.py"]
```

### Docker Compose:
```yaml
version: '3.8'
services:
  face-id:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./face_data:/app/face_data
      - ./cache:/app/cache
    restart: unless-stopped
    environment:
      - MONGODB_URI=${MONGODB_URI}
```

## 3. PM2 (Node.js Process Manager)

```bash
# PM2 o'rnatish
npm install -g pm2

# Python app uchun ecosystem file
# ecosystem.config.js
module.exports = {
  apps: [{
    name: 'face-id',
    script: 'python',
    args: 'main.py',
    cwd: '/path/to/face_id',
    interpreter: '/path/to/venv/bin/python',
    restart_delay: 5000,
    max_restarts: 10,
    autorestart: true,
    watch: false
  }]
}

# Ishga tushirish
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 4. SUPERVISOR (Python Process Manager)

### supervisor.conf:
```ini
[program:face-id]
command=/path/to/venv/bin/python main.py
directory=/path/to/face_id
user=your-username
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/face-id.log
```

## 5. CRON JOB (Backup va monitoring)

```bash
# crontab -e
# Har 5 daqiqada tizimni tekshirish
*/5 * * * * /path/to/check_face_id.sh

# Kun oxiri backup
0 0 * * * /path/to/backup_face_id.sh
```

### check_face_id.sh:
```bash
#!/bin/bash
if ! pgrep -f "python main.py" > /dev/null; then
    echo "Face ID to'xtagan, qayta ishga tushirish..."
    cd /path/to/face_id
    source venv/bin/activate
    nohup python main.py &
fi
```