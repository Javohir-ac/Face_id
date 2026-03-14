#!/usr/bin/env python3
"""
🌐 FACE ID WEB-ONLY VERSION FOR RENDER.COM
Faqat web interface, kamera yo'q
"""

import os
import json
from datetime import datetime, date, timedelta
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import io
import pymongo
from pymongo import MongoClient
import logging

# Logging sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
def get_mongodb_connection():
    """MongoDB ga ulanish"""
    try:
        mongodb_uri = os.environ.get('MONGODB_URI')
        if mongodb_uri:
            # SSL muammosini hal qilish uchun
            client = MongoClient(
                mongodb_uri,
                tls=True,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            # Connection test
            client.admin.command('ping')
            db = client.face_recognition_db
            logger.info("MongoDB ga muvaffaqiyatli ulandi")
            return db
        else:
            logger.warning("MONGODB_URI topilmadi, demo mode")
            return None
    except Exception as e:
        logger.error(f"MongoDB ulanish xatosi: {e}")
        logger.info("Demo mode da davom etiladi")
        return None

# Mock Face System for web-only
class WebOnlyFaceSystem:
    def __init__(self):
        self.is_running = True
        self.mongodb_db = get_mongodb_connection()
        self.current_users = self.load_current_users()
        self.known_face_names = self.load_known_users()
        
        # Mock data manager
        self.data_manager = WebDataManager(self.mongodb_db)
        
        logger.info(f"Web-only Face System initialized: {len(self.known_face_names)} users")
    
    def load_current_users(self):
        """Current users yuklash"""
        try:
            if self.mongodb_db is not None:
                # MongoDB dan yuklash
                system_doc = self.mongodb_db.system.find_one({'type': 'current_users'})
                if system_doc and 'data' in system_doc:
                    return list(system_doc['data'].keys())
            
            # Fallback: local file
            if os.path.exists('current_users.json'):
                with open('current_users.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return list(data.keys())
            
            # Demo data
            return ["Javohir", "Mehriddin"]
        except Exception as e:
            logger.error(f"Current users yuklash xatosi: {e}")
            return []
    
    def load_known_users(self):
        """Known users yuklash"""
        try:
            if self.mongodb_db is not None:
                # MongoDB dan yuklash
                users = list(self.mongodb_db.users.find({}, {'name': 1}))
                if users:
                    return [user['name'] for user in users]
            
            # Fallback: local file
            if os.path.exists('users.json'):
                with open('users.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return list(data.keys())
            
            # Demo data
            return ["Javohir", "Mehriddin", "Farizod", "Odinaxon", "Hosila", "Lochinbek", "Asilbek"]
        except Exception as e:
            logger.error(f"Known users yuklash xatosi: {e}")
            return ["Demo User 1", "Demo User 2", "Demo User 3"]
    
    def get_user_stats(self):
        """User statistikasi"""
        stats = []
        try:
            if self.mongodb_db is not None:
                # MongoDB dan real statistika
                for user in self.known_face_names:
                    user_doc = self.mongodb_db.users.find_one({'name': user})
                    if user_doc:
                        stats.append({
                            'name': user,
                            'total_entries': user_doc.get('total_entries', 0),
                            'total_time_minutes': user_doc.get('total_time_minutes', 0),
                            'is_inside': user in self.current_users,
                            'created_at': user_doc.get('created_at', datetime.now().isoformat())
                        })
                    else:
                        stats.append({
                            'name': user,
                            'total_entries': 0,
                            'total_time_minutes': 0,
                            'is_inside': user in self.current_users,
                            'created_at': datetime.now().isoformat()
                        })
            else:
                # Demo data
                for i, user in enumerate(self.known_face_names):
                    stats.append({
                        'name': user,
                        'total_entries': (i + 1) * 15,  # Demo data
                        'total_time_minutes': (i + 1) * 480,  # Demo: 8 soat
                        'is_inside': user in self.current_users,
                        'created_at': datetime.now().isoformat()
                    })
            
            return stats
        except Exception as e:
            logger.error(f"User stats xatosi: {e}")
            return []

class WebDataManager:
    def __init__(self, mongodb_db):
        self.mongodb_db = mongodb_db
        self.logs_data = [
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': 'Web-only mode ishga tushdi (Render.com)'
            }
        ]
    
    def get_daily_summary(self, target_date):
        """Kunlik hisobot"""
        try:
            if self.mongodb_db is not None:
                # MongoDB dan real ma'lumot
                start_date = datetime.combine(target_date, datetime.min.time())
                end_date = start_date + timedelta(days=1)
                
                attendance_records = list(self.mongodb_db.attendance.find({
                    'timestamp': {
                        '$gte': start_date.isoformat(),
                        '$lt': end_date.isoformat()
                    }
                }))
                
                # Ma'lumotlarni qayta ishlash
                users_summary = {}
                for record in attendance_records:
                    user_name = record['user_name']
                    if user_name not in users_summary:
                        users_summary[user_name] = {
                            'entries': [],
                            'sessions': [],
                            'total_minutes': 0
                        }
                    
                    users_summary[user_name]['entries'].append({
                        'time': datetime.fromisoformat(record['timestamp']).strftime('%H:%M'),
                        'action': record['action'],
                        'zone': record.get('zone', 'camera')
                    })
                
                # Sessiyalarni hisoblash
                for user_name, data in users_summary.items():
                    entries = data['entries']
                    sessions = []
                    current_session = None
                    
                    for entry in entries:
                        if entry['action'] == 'entry':
                            current_session = {'start': entry['time'], 'end': None, 'duration': 0}
                        elif entry['action'] == 'exit' and current_session:
                            current_session['end'] = entry['time']
                            
                            try:
                                start_time = datetime.strptime(current_session['start'], '%H:%M')
                                end_time = datetime.strptime(current_session['end'], '%H:%M')
                                duration = end_time - start_time
                                current_session['duration'] = int(duration.total_seconds() / 60)
                                
                                sessions.append(current_session)
                                data['total_minutes'] += current_session['duration']
                            except:
                                pass
                            
                            current_session = None
                    
                    data['sessions'] = sessions
                
                return {
                    'date': target_date.isoformat(),
                    'day_name': target_date.strftime('%A'),
                    'day_name_uz': self.get_uzbek_day_name(target_date.strftime('%A')),
                    'users': users_summary
                }
            else:
                # Demo data
                return self.get_demo_daily_summary(target_date)
                
        except Exception as e:
            logger.error(f"Daily summary xatosi: {e}")
            return self.get_demo_daily_summary(target_date)
    
    def get_demo_daily_summary(self, target_date):
        """Demo kunlik hisobot"""
        return {
            'date': target_date.isoformat(),
            'day_name': target_date.strftime('%A'),
            'day_name_uz': self.get_uzbek_day_name(target_date.strftime('%A')),
            'users': {
                'Javohir': {
                    'entries': [
                        {'time': '09:00', 'action': 'entry', 'zone': 'camera'},
                        {'time': '17:30', 'action': 'exit', 'zone': 'camera'}
                    ],
                    'sessions': [
                        {'start': '09:00', 'end': '17:30', 'duration': 510}
                    ],
                    'total_minutes': 510
                },
                'Mehriddin': {
                    'entries': [
                        {'time': '08:30', 'action': 'entry', 'zone': 'camera'},
                        {'time': '18:00', 'action': 'exit', 'zone': 'camera'}
                    ],
                    'sessions': [
                        {'start': '08:30', 'end': '18:00', 'duration': 570}
                    ],
                    'total_minutes': 570
                }
            }
        }
    
    def get_uzbek_day_name(self, english_day):
        """Inglizcha kun nomini o'zbekchaga o'girish"""
        days = {
            'Monday': 'Dushanba',
            'Tuesday': 'Seshanba', 
            'Wednesday': 'Chorshanba',
            'Thursday': 'Payshanba',
            'Friday': 'Juma',
            'Saturday': 'Shanba',
            'Sunday': 'Yakshanba'
        }
        return days.get(english_day, english_day)
    
    def create_backup(self):
        """Backup yaratish (mock)"""
        return f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Flask app yaratish
def create_render_app():
    app = Flask(__name__)
    CORS(app)  # CORS yoqish
    
    # Face system
    face_system = WebOnlyFaceSystem()
    
    @app.route('/')
    def dashboard():
        """Asosiy dashboard"""
        return '''
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Face ID Dashboard - Render.com</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: #333;
                }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .header { 
                    background: rgba(255,255,255,0.95); 
                    padding: 30px; 
                    border-radius: 15px; 
                    margin-bottom: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    text-align: center;
                }
                .header h1 { color: #2c3e50; font-size: 2.5em; margin-bottom: 10px; }
                .header p { color: #7f8c8d; font-size: 1.1em; }
                .stats { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
                    gap: 25px; 
                    margin-bottom: 30px; 
                }
                .stat-card { 
                    background: rgba(255,255,255,0.95); 
                    padding: 30px; 
                    border-radius: 15px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    text-align: center;
                    transition: transform 0.3s ease;
                }
                .stat-card:hover { transform: translateY(-5px); }
                .stat-number { 
                    font-size: 3em; 
                    font-weight: bold; 
                    background: linear-gradient(45deg, #3498db, #2980b9);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }
                .stat-label { color: #7f8c8d; font-size: 1.1em; font-weight: 500; }
                .users-section { 
                    background: rgba(255,255,255,0.95); 
                    padding: 30px; 
                    border-radius: 15px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    margin-bottom: 30px;
                }
                .users-section h3 { 
                    color: #2c3e50; 
                    margin-bottom: 20px; 
                    font-size: 1.5em;
                    border-bottom: 2px solid #ecf0f1;
                    padding-bottom: 10px;
                }
                .user-item { 
                    padding: 15px; 
                    border-bottom: 1px solid #ecf0f1; 
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center;
                    transition: background 0.3s ease;
                }
                .user-item:hover { background: #f8f9fa; }
                .user-item:last-child { border-bottom: none; }
                .user-name { font-weight: 600; color: #2c3e50; }
                .status-inside { 
                    color: #27ae60; 
                    font-weight: bold; 
                    background: #d5f4e6;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-size: 0.9em;
                }
                .status-outside { 
                    color: #e74c3c; 
                    background: #fdeaea;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-size: 0.9em;
                }
                .controls { 
                    display: flex; 
                    gap: 15px; 
                    justify-content: center; 
                    flex-wrap: wrap;
                    margin-bottom: 30px;
                }
                .btn { 
                    background: linear-gradient(45deg, #3498db, #2980b9);
                    color: white; 
                    padding: 12px 25px; 
                    border: none; 
                    border-radius: 25px; 
                    cursor: pointer;
                    font-size: 1em;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    display: inline-block;
                }
                .btn:hover { 
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
                }
                .btn-success { background: linear-gradient(45deg, #27ae60, #229954); }
                .btn-info { background: linear-gradient(45deg, #17a2b8, #138496); }
                .loading { 
                    text-align: center; 
                    color: #7f8c8d; 
                    font-style: italic;
                    padding: 20px;
                }
                .footer {
                    text-align: center;
                    color: rgba(255,255,255,0.8);
                    margin-top: 30px;
                    padding: 20px;
                }
                
                /* Mobile responsive */
                @media (max-width: 768px) {
                    .container { padding: 15px; }
                    .header h1 { font-size: 2em; }
                    .stat-number { font-size: 2.5em; }
                    .stats { grid-template-columns: 1fr; }
                    .controls { flex-direction: column; align-items: center; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Face ID Dashboard</h1>
                    <p>Render.com da deploy qilingan web-only versiya</p>
                </div>
                
                <div class="stats" id="stats">
                    <div class="loading">Ma'lumotlar yuklanmoqda...</div>
                </div>
                
                <div class="users-section">
                    <h3>👥 Foydalanuvchilar Ro'yxati</h3>
                    <div id="users">
                        <div class="loading">Foydalanuvchilar yuklanmoqda...</div>
                    </div>
                </div>
                
                <div class="controls">
                    <button class="btn" onclick="loadData()">🔄 Yangilash</button>
                    <a href="/api/status" class="btn btn-info" target="_blank">📊 API Status</a>
                    <a href="/health" class="btn btn-success" target="_blank">❤️ Health Check</a>
                </div>
                
                <div class="footer">
                    <p>🚀 Powered by Render.com | 🛡️ Robust Face ID System</p>
                    <p>Last updated: <span id="lastUpdate">-</span></p>
                </div>
            </div>
            
            <script>
                function loadData() {
                    document.getElementById('lastUpdate').textContent = new Date().toLocaleString('uz-UZ');
                    
                    // Stats yuklash
                    fetch('/api/dashboard-data')
                        .then(response => response.json())
                        .then(data => {
                            // Stats
                            document.getElementById('stats').innerHTML = `
                                <div class="stat-card">
                                    <div class="stat-number">${data.status.total_users}</div>
                                    <div class="stat-label">Jami Foydalanuvchilar</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-number">${data.status.current_users.length}</div>
                                    <div class="stat-label">Hozir Ichkarida</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-number">${data.today_entries || 0}</div>
                                    <div class="stat-label">Bugungi Kirishlar</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-number">${data.status.is_running ? '✅' : '❌'}</div>
                                    <div class="stat-label">Tizim Holati</div>
                                </div>
                            `;
                            
                            // Users list
                            let usersHtml = '';
                            if (data.users && data.users.length > 0) {
                                data.users.forEach(user => {
                                    const status = user.is_inside ? 
                                        '<span class="status-inside">Ichkarida</span>' : 
                                        '<span class="status-outside">Tashqarida</span>';
                                    const totalHours = Math.floor(user.total_time_minutes / 60);
                                    const totalMins = user.total_time_minutes % 60;
                                    usersHtml += `
                                        <div class="user-item">
                                            <div>
                                                <div class="user-name">${user.name}</div>
                                                <small style="color: #7f8c8d;">
                                                    ${user.total_entries} ta kirish | ${totalHours}:${totalMins.toString().padStart(2, '0')} soat
                                                </small>
                                            </div>
                                            <div>${status}</div>
                                        </div>
                                    `;
                                });
                            } else {
                                usersHtml = '<div class="loading">Foydalanuvchilar topilmadi</div>';
                            }
                            document.getElementById('users').innerHTML = usersHtml;
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            document.getElementById('stats').innerHTML = '<div class="loading">❌ Ma\'lumot yuklashda xatolik</div>';
                            document.getElementById('users').innerHTML = '<div class="loading">❌ Foydalanuvchilar yuklashda xatolik</div>';
                        });
                }
                
                // Sahifa yuklanganda ma'lumotlarni yuklash
                loadData();
                
                // Har 30 soniyada yangilash
                setInterval(loadData, 30000);
            </script>
        </body>
        </html>
        '''
    
    @app.route('/api/dashboard-data')
    def api_dashboard_data():
        """Dashboard ma'lumotlari"""
        try:
            daily_summary = face_system.data_manager.get_daily_summary(date.today())
            today_entries = 0
            if daily_summary.get('users'):
                for user_data in daily_summary['users'].values():
                    today_entries += len(user_data.get('sessions', []))
            
            return jsonify({
                'status': {
                    'is_running': face_system.is_running,
                    'current_users': face_system.current_users,
                    'total_users': len(face_system.known_face_names),
                    'current_time': datetime.now().isoformat()
                },
                'users': face_system.get_user_stats(),
                'daily_summary': daily_summary,
                'today_entries': today_entries
            })
        except Exception as e:
            logger.error(f"Dashboard data error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/status')
    def api_status():
        """Tizim holati"""
        return jsonify({
            'is_running': face_system.is_running,
            'current_users': face_system.current_users,
            'total_users': len(face_system.known_face_names),
            'current_time': datetime.now().isoformat(),
            'mode': 'web-only',
            'platform': 'render.com',
            'mongodb_connected': face_system.mongodb_db is not None,
            'version': '2.0.0'
        })
    
    @app.route('/health')
    def health_check():
        """Health check for Render"""
        try:
            # MongoDB connection test
            mongodb_status = 'connected' if face_system.mongodb_db else 'disconnected'
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'face-id-web',
                'mongodb': mongodb_status,
                'users_count': len(face_system.known_face_names),
                'current_users_count': len(face_system.current_users)
            })
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/users')
    def api_users():
        """Foydalanuvchilar ro'yxati"""
        try:
            return jsonify(face_system.get_user_stats())
        except Exception as e:
            logger.error(f"Users API error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/daily-summary')
    def api_daily_summary():
        """Kunlik hisobot"""
        try:
            date_param = request.args.get('date')
            if date_param:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            else:
                target_date = date.today()
            
            summary = face_system.data_manager.get_daily_summary(target_date)
            return jsonify(summary)
        except Exception as e:
            logger.error(f"Daily summary error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint topilmadi'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Server xatosi'}), 500
    
    return app

# Render uchun app yaratish
app = create_render_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Face ID Web starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)