from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)  # מאפשר בקשות מכל מקור

# נתוני משתמשים (זמני)
users = {
    "headquarters": {"password": "admin123", "role": "admin", "name": "מטה ראשי"},
    "haifa_user": {"password": "haifa123", "role": "manager", "name": "סניף חיפה"}
}

# נתונים זמניים למסעדות
restaurants_data = {
    "headquarters": {
        "name": "מטה ראשי",
        "chefs": [
            {"name": "אמיר כהן", "rating": 9.2, "last_check": "2024-09-25"},
            {"name": "שרה לוי", "rating": 8.8, "last_check": "2024-09-24"}
        ],
        "tasks": [
            {"task": "בדיקת איכות בוקר", "status": "completed", "date": "2024-09-27"},
            {"task": "הכשרת טבח חדש", "status": "pending", "date": "2024-09-28"}
        ]
    },
    "haifa_user": {
        "name": "סניף חיפה", 
        "chefs": [
            {"name": "יוסי מזרחי", "rating": 8.5, "last_check": "2024-09-26"},
            {"name": "רחל אברהם", "rating": 9.0, "last_check": "2024-09-25"}
        ],
        "tasks": [
            {"task": "ניקיון מטבח", "status": "completed", "date": "2024-09-27"},
            {"task": "הזמנת חומרי גלם", "status": "pending", "date": "2024-09-28"}
        ]
    }
}

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Giraffe - מערכת ניהול מטבח</title>
    <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Assistant', sans-serif;
            background: linear-gradient(135deg, #f5f1a8 0%, #e8e19a 100%);
            min-height: 100vh;
            direction: rtl;
        }

        .container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }

        .login-card, .dashboard-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }

        .dashboard-card {
            max-width: 800px;
            text-align: right;
        }

        .logo {
            font-size: 3rem;
            margin-bottom: 10px;
        }

        .title {
            font-size: 2rem;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #718096;
            margin-bottom: 30px;
            font-size: 1.1rem;
        }

        .form-group {
            margin-bottom: 20px;
            text-align: right;
        }

        .form-label {
            display: block;
            margin-bottom: 8px;
            color: #4a5568;
            font-weight: 600;
        }

        .form-input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 1rem;
            font-family: 'Assistant', sans-serif;
            transition: border-color 0.3s;
        }

        .form-input:focus {
            outline: none;
            border-color: #4c7c54;
        }

        .login-btn {
            width: 100%;
            background: #4c7c54;
            color: white;
            border: none;
            padding: 14px;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            margin-bottom: 20px;
        }

        .login-btn:hover {
            background: #3d6444;
        }

        .login-btn:disabled {
            background: #a0aec0;
            cursor: not-allowed;
        }

        .error-message {
            color: #e53e3e;
            margin-top: 10px;
            font-weight: 500;
        }

        .success-message {
            color: #38a169;
            margin-top: 10px;
            font-weight: 500;
        }

        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }

        .welcome-text {
            font-size: 1.5rem;
            font-weight: 700;
            color: #2d3748;
        }

        .logout-btn {
            background: #e53e3e;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }

        .logout-btn:hover {
            background: #c53030;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: #f7fafc;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        }

        .stat-title {
            font-size: 0.9rem;
            color: #718096;
            margin-bottom: 8px;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #2d3748;
        }

        .section {
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }

        .section-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 20px;
        }

        .chef-item, .task-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: #f7fafc;
            border-radius: 8px;
            margin-bottom: 10px;
        }

        .chef-info, .task-info {
            flex: 1;
        }

        .chef-name, .task-name {
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 4px;
        }

        .chef-rating {
            color: #4c7c54;
            font-weight: 700;
        }

        .task-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }

        .status-completed {
            background: #c6f6d5;
            color: #22543d;
        }

        .status-pending {
            background: #fed7c3;
            color: #9c4221;
        }

        .hidden {
            display: none;
        }

        .loading {
            opacity: 0.7;
            pointer-events: none;
        }

        @media (max-width: 600px) {
            .dashboard-card {
                padding: 20px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- מסך התחברות -->
        <div id="loginScreen" class="login-card">
            <div class="logo">🦒</div>
            <h1 class="title">Giraffe</h1>
            <p class="subtitle">מערכת ניהול מטבח</p>
            
            <form id="loginForm">
                <div class="form-group">
                    <label class="form-label">שם משתמש</label>
                    <input type="text" id="username" class="form-input" placeholder="headquarters / haifa_user" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label">סיסמה</label>
                    <input type="password" id="password" class="form-input" placeholder="admin123 / haifa123" required>
                </div>
                
                <button type="submit" id="loginBtn" class="login-btn">התחבר</button>
                
                <div id="loginMessage"></div>
            </form>
            
            <div style="margin-top: 30px; color: #718096; font-size: 0.9rem;">
                <strong>פרטי התחברות לדוגמה:</strong><br>
                headquarters / admin123<br>
                haifa_user / haifa123
            </div>
        </div>

        <!-- דשבורד -->
        <div id="dashboard" class="dashboard-card hidden">
            <div class="dashboard-header">
                <div class="welcome-text">ברוך הבא, <span id="userName"></span></div>
                <button id="logoutBtn" class="logout-btn">התנתק</button>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-title">טבחים פעילים</div>
                    <div class="stat-value" id="totalChefs">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">ציון ממוצע</div>
                    <div class="stat-value" id="avgRating">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">משימות השלמו</div>
                    <div class="stat-value" id="completedTasks">0</div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">טבחים במערכת</h2>
                <div id="chefsList"></div>
            </div>

            <div class="section">
                <h2 class="section-title">משימות השבוע</h2>
                <div id="tasksList"></div>
            </div>
        </div>
    </div>

    <script>
        // משתנים גלובליים
        let currentUser = null;
        const API_BASE = window.location.origin;

        // אלמנטים
        const loginScreen = document.getElementById('loginScreen');
        const dashboard = document.getElementById('dashboard');
        const loginForm = document.getElementById('loginForm');
        const loginBtn = document.getElementById('loginBtn');
        const loginMessage = document.getElementById('loginMessage');
        const logoutBtn = document.getElementById('logoutBtn');
        const userName = document.getElementById('userName');

        // התחברות
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            loginBtn.disabled = true;
            loginBtn.textContent = 'מתחבר...';
            loginMessage.innerHTML = '';
            
            try {
                const response = await fetch(`${API_BASE}/api/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentUser = data.user;
                    showDashboard();
                    loginMessage.innerHTML = '<div class="success-message">התחברות הצליחה!</div>';
                } else {
                    loginMessage.innerHTML = `<div class="error-message">${data.message}</div>`;
                }
            } catch (error) {
                console.error('Login error:', error);
                loginMessage.innerHTML = '<div class="error-message">שגיאה בהתחברות. נסה שוב.</div>';
            }
            
            loginBtn.disabled = false;
            loginBtn.textContent = 'התחבר';
        });

        // התנתקות
        logoutBtn.addEventListener('click', () => {
            currentUser = null;
            showLogin();
            document.getElementById('loginForm').reset();
            loginMessage.innerHTML = '';
        });

        // הצגת מסך התחברות
        function showLogin() {
            loginScreen.classList.remove('hidden');
            dashboard.classList.add('hidden');
        }

        // הצגת דשבורד
        function showDashboard() {
            loginScreen.classList.add('hidden');
            dashboard.classList.remove('hidden');
            userName.textContent = currentUser.name;
            loadDashboardData();
        }

        // טעינת נתוני דשבורד
        async function loadDashboardData() {
            try {
                const response = await fetch(`${API_BASE}/api/dashboard/${currentUser.username}`);
                const data = await response.json();
                
                if (data.success) {
                    updateDashboard(data.data);
                }
            } catch (error) {
                console.error('Dashboard error:', error);
            }
        }

        // עדכון דשבורד
        function updateDashboard(data) {
            // סטטיסטיקות
            document.getElementById('totalChefs').textContent = data.chefs.length;
            
            const avgRating = data.chefs.reduce((sum, chef) => sum + chef.rating, 0) / data.chefs.length;
            document.getElementById('avgRating').textContent = avgRating.toFixed(1);
            
            const completed = data.tasks.filter(task => task.status === 'completed').length;
            document.getElementById('completedTasks').textContent = `${completed}/${data.tasks.length}`;

            // רשימת טבחים
            const chefsList = document.getElementById('chefsList');
            chefsList.innerHTML = data.chefs.map(chef => `
                <div class="chef-item">
                    <div class="chef-info">
                        <div class="chef-name">${chef.name}</div>
                        <div style="color: #718096; font-size: 0.9rem;">בדיקה אחרונה: ${chef.last_check}</div>
                    </div>
                    <div class="chef-rating">${chef.rating}/10</div>
                </div>
            `).join('');

            // רשימת משימות
            const tasksList = document.getElementById('tasksList');
            tasksList.innerHTML = data.tasks.map(task => `
                <div class="task-item">
                    <div class="task-info">
                        <div class="task-name">${task.task}</div>
                        <div style="color: #718096; font-size: 0.9rem;">${task.date}</div>
                    </div>
                    <div class="task-status status-${task.status}">
                        ${task.status === 'completed' ? 'הושלם' : 'בהמתנה'}
                    </div>
                </div>
            `).join('');
        }

        // בדיקת חיבור לשרת
        async function checkConnection() {
            try {
                const response = await fetch(`${API_BASE}/`);
                const data = await response.json();
                console.log('✅ החיבור לשרת תקין:', data.message);
            } catch (error) {
                console.error('❌ שגיאה בחיבור לשרת:', error);
            }
        }

        // אתחול
        checkConnection();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """עמוד הבית - מחזיר את הפרונטאנד"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def status():
    """בדיקת סטטוס השרת"""
    return jsonify({
        "message": "Kitchen Management API - זמין מערכת איכות",
        "data": {"version": "1.0.0"},
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/login', methods=['POST'])
def login():
    """התחברות למערכת"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if username in users and users[username]['password'] == password:
            user_data = users[username].copy()
            user_data['username'] = username
            return jsonify({
                "success": True,
                "message": "התחברות הצליחה",
                "user": user_data
            })
        else:
            return jsonify({
                "success": False,
                "message": "שם משתמש או סיסמה שגויים"
            }), 401
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "שגיאה בהתחברות"
        }), 500

@app.route('/api/dashboard/<username>')
def get_dashboard(username):
    """קבלת נתוני דשבורד"""
    try:
        if username in restaurants_data:
            return jsonify({
                "success": True,
                "data": restaurants_data[username]
            })
        else:
            return jsonify({
                "success": False,
                "message": "משתמש לא נמצא"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "שגיאה בקבלת נתונים"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)