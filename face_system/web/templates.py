"""
Modern Professional HTML Templates
"""

def get_dashboard_html():
    """Excel-style Simple Dashboard - Faqat muhim ma'lumotlar"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Face Recognition System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f8f9fa;
            color: #333;
            line-height: 1.4;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header-controls {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .date-controls {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .date-input {
            padding: 8px 12px;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            font-size: 0.9rem;
            font-family: inherit;
            background: white;
            color: #495057;
            transition: border-color 0.2s ease;
        }
        
        .date-input:focus {
            outline: none;
            border-color: #28a745;
            box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.1);
        }
        
        .export-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
        }
        
        .export-btn:hover {
            background: #218838;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
        }
        
        .export-btn:active {
            transform: translateY(0);
        }
        
        .export-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .header h1 {
            font-size: 1.5rem;
            color: #2c3e50;
            font-weight: 600;
        }
        
        .status {
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .status.online {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .main-table {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .table-header {
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 2px solid #dee2e6;
            font-weight: 600;
            color: #495057;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }
        
        th {
            background: #f1f3f4;
            padding: 15px 20px;
            text-align: left;
            font-weight: 600;
            color: #5f6368;
            border-bottom: 2px solid #e8eaed;
            font-size: 0.9rem;
            white-space: nowrap;
        }
        
        th:nth-child(1) { width: 25%; } /* Ism */
        th:nth-child(2) { width: 15%; text-align: center; } /* Holat */
        th:nth-child(3) { width: 15%; text-align: center; } /* Bugun kirish */
        th:nth-child(4) { width: 20%; text-align: center; } /* Bugun jami */
        th:nth-child(5) { width: 25%; text-align: center; } /* Oxirgi faollik */
        
        td {
            padding: 15px 20px;
            border-bottom: 1px solid #e8eaed;
            font-size: 0.9rem;
            vertical-align: middle;
        }
        
        td:nth-child(1) { font-weight: 600; color: #2c3e50; } /* Ism */
        td:nth-child(2) { text-align: center; } /* Holat */
        td:nth-child(3) { text-align: center; font-weight: 500; } /* Bugun kirish */
        td:nth-child(4) { text-align: center; font-family: 'Courier New', monospace; font-weight: 500; } /* Bugun jami */
        td:nth-child(5) { text-align: center; font-family: 'Courier New', monospace; font-size: 0.85rem; } /* Oxirgi faollik */
        
        tr:hover {
            background: #f8f9fa;
            transition: background-color 0.2s ease;
        }
        
        tr:nth-child(even) {
            background: #fafbfc;
        }
        
        tr:nth-child(even):hover {
            background: #f0f2f5;
        }
        
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-align: center;
            min-width: 80px;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-inside {
            background: #e8f5e8;
            color: #2e7d32;
            border: 2px solid #4caf50;
        }
        
        .badge-outside {
            background: #ffebee;
            color: #c62828;
            border: 2px solid #f44336;
        }
        
        .time-cell {
            font-family: 'Courier New', monospace;
            font-weight: 500;
        }
        
        .number-cell {
            text-align: center;
            font-weight: 600;
            color: #1976d2;
        }
        
        .name-cell {
            font-weight: 600;
            color: #2c3e50;
            font-size: 1rem;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-style: italic;
        }
        
        .refresh-info {
            text-align: center;
            margin-top: 15px;
            color: #6c757d;
            font-size: 0.8rem;
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header { 
                flex-direction: column; 
                gap: 15px; 
                text-align: center;
            }
            .header-controls {
                flex-direction: column;
                gap: 15px;
                width: 100%;
            }
            .date-controls {
                flex-direction: column;
                gap: 10px;
                width: 100%;
            }
            .date-input {
                width: 100%;
            }
            .export-btn {
                width: 100%;
                justify-content: center;
            }
            table { font-size: 0.8rem; }
            th, td { padding: 8px 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Face Recognition System</h1>
            <div class="header-controls">
                <div class="date-controls">
                    <input type="date" id="reportDate" class="date-input">
                    <button id="exportExcel" class="export-btn">📊 Excel yuklab olish</button>
                </div>
                <div id="systemStatus" class="status">Loading...</div>
            </div>
        </div>
        
        <div class="main-table">
            <div class="table-header">
                Foydalanuvchilar ro'yxati va faollik
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>👤 Ism</th>
                        <th>📍 Holat</th>
                        <th>🔢 Bugun kirish</th>
                        <th>⏱️ Bugun jami</th>
                        <th>🕐 Oxirgi faollik</th>
                    </tr>
                </thead>
                <tbody id="usersTable">
                    <tr>
                        <td colspan="5" class="empty-state">Ma'lumotlar yuklanmoqda...</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="refresh-info">
            Ma'lumotlar har 3 soniyada yangilanadi
        </div>
    </div>

    <script>
        function formatTime(minutes) {
            if (minutes < 60) return minutes + 'm';
            const hours = Math.floor(minutes / 60);
            const mins = minutes % 60;
            return hours + 'h ' + (mins > 0 ? mins + 'm' : '');
        }
        
        function formatDateTime(dateStr) {
            if (!dateStr) return '-';
            const date = new Date(dateStr);
            return date.toLocaleString('uz-UZ', { 
                day: '2-digit',
                month: '2-digit', 
                hour: '2-digit', 
                minute: '2-digit'
            });
        }
        
        function updateDashboard() {
            fetch('/api/dashboard-data')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('API Error:', data.error);
                        return;
                    }
                    
                    // System status
                    const statusEl = document.getElementById('systemStatus');
                    if (data.status.is_running) {
                        statusEl.textContent = 'Tizim faol (' + data.status.total_users + ' foydalanuvchi)';
                        statusEl.className = 'status online';
                    } else {
                        statusEl.textContent = 'Tizim faol emas';
                        statusEl.className = 'status offline';
                    }
                    
                    // Users table
                    const tableBody = document.getElementById('usersTable');
                    
                    if (data.users.length === 0) {
                        tableBody.innerHTML = '<tr><td colspan="5" class="empty-state">Hech qanday foydalanuvchi royxatdan otmagan</td></tr>';
                        return;
                    }
                    
                    // Get today's activity for last activity
                    const dailySummary = data.daily_summary;
                    
                    tableBody.innerHTML = data.users.map(user => {
                        const statusBadge = user.is_inside ? 
                            '<span class="status-badge badge-inside">Ichkarida</span>' : 
                            '<span class="status-badge badge-outside">Tashqarida</span>';
                        
                        const currentDuration = user.is_inside ? formatTime(user.current_duration_minutes) : '-';
                        
                        // Get user's today activity for last activity
                        let lastActivity = '-';
                        if (dailySummary.users && dailySummary.users[user.name]) {
                            const sessions = dailySummary.users[user.name].sessions;
                            if (sessions.length > 0) {
                                const lastSession = sessions[sessions.length - 1];
                                if (lastSession.end === 'Hali ichkarida') {
                                    lastActivity = lastSession.start + ' (kirdi)';
                                } else {
                                    lastActivity = lastSession.end + ' (chiqdi)';
                                }
                            }
                        }
                        
                        const todayTotal = dailySummary.users && dailySummary.users[user.name] ? 
                            formatTime(dailySummary.users[user.name].total_minutes) : '0m';
                        
                        return `
                            <tr>
                                <td class="name-cell">${user.name}</td>
                                <td>${statusBadge}</td>
                                <td class="number-cell">${user.today_entries}</td>
                                <td class="time-cell">${todayTotal}</td>
                                <td class="time-cell">${lastActivity}</td>
                            </tr>
                        `;
                    }).join('');
                })
                .catch(error => {
                    console.error('Dashboard update error:', error);
                    document.getElementById('systemStatus').textContent = 'Ulanish xatosi';
                    document.getElementById('systemStatus').className = 'status offline';
                });
        }
        
        function exportToExcel() {
            const dateInput = document.getElementById('reportDate');
            const selectedDate = dateInput.value || new Date().toISOString().split('T')[0];
            const exportBtn = document.getElementById('exportExcel');
            
            // Button holatini o'zgartirish
            const originalText = exportBtn.innerHTML;
            exportBtn.innerHTML = '⏳ Yuklanmoqda...';
            exportBtn.disabled = true;
            
            // Excel faylni yuklab olish
            window.location.href = `/api/export-excel?date=${selectedDate}`;
            
            // Button holatini qaytarish
            setTimeout(() => {
                exportBtn.innerHTML = originalText;
                exportBtn.disabled = false;
            }, 2000);
        }
        
        // Event listeners
        document.addEventListener('DOMContentLoaded', function() {
            // Bugungi sanani default qilib qo'yish
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('reportDate').value = today;
            
            // Export button event
            document.getElementById('exportExcel').addEventListener('click', exportToExcel);
        });
        
        updateDashboard();
        setInterval(updateDashboard, 3000);
    </script>
</body>
</html>
    '''