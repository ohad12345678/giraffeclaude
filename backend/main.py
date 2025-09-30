from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# נתוני משתמשים
users = {
    "headquarters": {"password": "admin123", "role": "admin", "name": "מטה ראשי"},
    "haifa_user": {"password": "haifa123", "role": "manager", "name": "סניף חיפה"}
}

# נתונים זמניים
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Giraffe - מערכת ניהול מטבח</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif; 
            background: #f5f1a8; 
            min-height: 100vh; 
            direction: rtl;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container { 
            background: white; 
            padding: 40px; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 400px;
            text-align: center;
        }
        .logo { font-size: 3rem; margin-bottom: 20px; }
        .title { font-size: 2rem; color: #2d3748; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; text-align: right; }
        .form-label { display: block; margin-bottom: 8px; color: #4a5568; font-weight: bold; }
        .form-input { 
            width: 100%; 
            padding: 12px; 
            border: 2px solid #e2e8f0; 
            border-radius: 10px; 
            font-size: 1rem;
        }
        .login-btn { 
            width: 100%; 
            background: #4c7c54; 
            color: white; 
            border: none; 
            padding: 14px; 
            border-radius: 10px; 
            font-size: 1.1rem; 
            cursor: pointer; 
            margin-bottom: 20px;
        }
        .login-btn:hover { background: #3d6444; }
        .message { margin-top: 10px; font-weight: bold; }
        .error { color: #e53e3e; }
        .success { color: #38a169; }
        .demo-info { 
            margin-top: 30px; 
            color: #718096; 
            font-size: 0.9rem; 
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🦒</div>
        <h1 class="title">Giraffe - מערכת ניהול מטבח</h1>
        
        <form id="loginForm">
            <div class="form-group">
                <label class="form-label">שם משתמש</label>
                <input type="text" id="username" class="form-input" placeholder="headquarters / haifa_user" required>
            </div>
            
            <div class="form-group">
                <label class="form-label">סיסמה</label>
                <input type="password" id="password" class="form-input" placeholder="admin123 / haifa123" required>
            </div>
            
            <button type="submit" class="login-btn">התחבר</button>
            
            <div id="message"></div>
        </form>
        
        <div class="demo-info">
            <strong>פרטי התחברות לדוגמה:</strong><br>
            headquarters / admin123<br>
            haifa_user / haifa123
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const messageDiv = document.getElementById('message');
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    messageDiv.innerHTML = '<div class="message success">התחברות הצליחה! ✅</div>';
                    setTimeout(() => {
                        alert('ברוך הבא למערכת ' + data.user.name + '!\\nהמערכת פועלת בהצלחה.');
                    }, 1000);
                } else {
                    messageDiv.innerHTML = '<div class="message error">' + data.message + '</div>';
                }
            } catch (error) {
                messageDiv.innerHTML = '<div class="message error">שגיאה בהתחברות</div>';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def login():
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

@app.route('/api/status')
def status():
    return jsonify({
        "message": "Kitchen Management API - מערכת פועלת!",
        "data": {"version": "1.0.0"},
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)