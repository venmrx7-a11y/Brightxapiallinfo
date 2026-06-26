from flask import Flask, render_template_string, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
import json

app = Flask(__name__)
app.secret_key = "bright_x_info_secret"

# Database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "bright_x_info.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ============ API CONFIG ============
API_TOKEN = "knowncoder"
API_NUM2INFO = "https://spyshadow.site/api/num2info.php"
API_TG2NUM = "https://spyshadow.site/api/tg-to-num.php"

# ============ ACCESS KEYS ============
WEB_ACCESS_KEY = "BRIGHT-X-OWNER"
ADMIN_ACCESS_KEY = "VENOM-X-OWNER"

# ============ DATABASE MODELS ============
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned = db.Column(db.Boolean, default=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_super = db.Column(db.Boolean, default=False)

# Create tables
with app.app_context():
    db.create_all()
    
    # Default admin
    admin = Admin.query.filter_by(username="VENOM-X-OWNER").first()
    if not admin:
        admin = Admin(username="VENOM-X-OWNER", password="VENOM-X-OWNER", is_super=True)
        db.session.add(admin)
        db.session.commit()

# ============ STYLISH TEXT FUNCTION ============
def to_fancy(text):
    fancy_map = {
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇', 'I': '𝐈',
        'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑',
        'S': '𝐒', 'T': '𝐓', 'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠', 'h': '𝐡', 'i': '𝐢',
        'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧', 'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫',
        's': '𝐬', 't': '𝐭', 'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳',
        '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
    }
    return ''.join(fancy_map.get(c, c) for c in text)

# ============ HELPER FUNCTIONS ============
def get_num_info(number):
    try:
        url = f"{API_NUM2INFO}?num={number}&token={API_TOKEN}"
        response = requests.get(url, timeout=15)
        return response.json()
    except:
        return {"status": False, "error": "API Error"}

def get_tg_info(user_id):
    try:
        url = f"{API_TG2NUM}?q={user_id}&token={API_TOKEN}"
        response = requests.get(url, timeout=15)
        return response.json()
    except:
        return {"status": False, "error": "API Error"}

def register_user(user_id, username=None, ip=None):
    user = User.query.filter_by(user_id=str(user_id)).first()
    if not user:
        user = User(user_id=str(user_id), username=username, ip_address=ip)
        db.session.add(user)
        db.session.commit()
    return user

def is_banned(user_id):
    user = User.query.filter_by(user_id=str(user_id)).first()
    return user and user.is_banned

# ============ HTML TEMPLATES ============
KEY_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BRIGHT X INFO</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Orbitron', monospace; }
        body { min-height: 100vh; background: #0a0a0a; display: flex; justify-content: center; align-items: center; position: relative; overflow: hidden; }
        body::before { content: ''; position: absolute; width: 200%; height: 200%; background: radial-gradient(circle, rgba(0,255,0,0.05) 0%, transparent 60%); animation: rotate 25s linear infinite; z-index: 0; }
        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .card { position: relative; z-index: 1; background: rgba(0,0,0,0.95); border-radius: 30px; padding: 50px 40px; width: 100%; max-width: 450px; border: 1px solid rgba(0,255,0,0.3); box-shadow: 0 0 50px rgba(0,255,0,0.1); }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { font-size: 28px; font-weight: 800; letter-spacing: 4px; color: #00ff00; text-shadow: 0 0 10px rgba(0,255,0,0.5); }
        .logo p { color: rgba(0,255,0,0.5); font-size: 11px; letter-spacing: 3px; margin-top: 5px; }
        .sub { color: rgba(0,255,0,0.6); text-align: center; font-size: 12px; margin-bottom: 30px; letter-spacing: 2px; }
        .input-group { margin-bottom: 22px; }
        .input-group input { width: 100%; padding: 15px 20px; background: rgba(0,255,0,0.05); border: 1px solid rgba(0,255,0,0.3); border-radius: 15px; color: #00ff00; font-size: 14px; letter-spacing: 1px; }
        .input-group input:focus { outline: none; border-color: #00ff00; box-shadow: 0 0 20px rgba(0,255,0,0.2); }
        .input-group input::placeholder { color: rgba(0,255,0,0.3); }
        .btn { width: 100%; padding: 15px; background: linear-gradient(135deg, #00ff00, #009900); border: none; border-radius: 15px; color: #0a0a0a; font-size: 16px; font-weight: 800; letter-spacing: 2px; cursor: pointer; transition: 0.3s; }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,255,0,0.3); }
        .error { background: rgba(255,0,0,0.2); border: 1px solid #ff0000; border-radius: 12px; padding: 12px; margin-bottom: 20px; text-align: center; color: #ff6666; font-size: 12px; }
        .footer { text-align: center; margin-top: 30px; font-size: 9px; color: rgba(0,255,0,0.25); }
        .admin-link { color: rgba(0,255,0,0.3); text-decoration: none; font-size: 10px; display: block; margin-top: 15px; }
        .admin-link:hover { color: #00ff00; }
        .typing { color: #00ff00; font-size: 12px; animation: blink 1s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">
            <h1>{{ fancy_title }}</h1>
            <p>ACCESS GRANTED</p>
        </div>
        <p class="sub">ENTER KEY TO ACCESS</p>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST" action="/verify-key">
            <div class="input-group">
                <input type="text" name="key" placeholder="ENTER ACCESS KEY" required autofocus>
            </div>
            <button type="submit" class="btn">ACCESS</button>
        </form>
        
        <a href="/admin-login" class="admin-link">ADMIN PANEL</a>
        <div class="footer">2025 BRIGHT X INFO</div>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BRIGHT X INFO</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Orbitron', monospace; }
        body { background: #0a0a0a; min-height: 100vh; }
        .navbar { background: rgba(0,0,0,0.95); padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #00ff00; }
        .navbar h1 { font-size: 20px; letter-spacing: 2px; color: #00ff00; text-shadow: 0 0 10px rgba(0,255,0,0.3); }
        .nav-links a { color: #00ff00; text-decoration: none; margin-left: 20px; font-size: 12px; }
        .container { padding: 30px; max-width: 1200px; margin: 0 auto; }
        .options { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px; }
        @media(max-width:768px){ .options { grid-template-columns: 1fr; } }
        .option-card { background: rgba(0,0,0,0.8); border-radius: 20px; padding: 30px; border: 1px solid rgba(0,255,0,0.3); }
        .option-card h2 { color: #00ff00; font-size: 18px; margin-bottom: 20px; letter-spacing: 2px; text-shadow: 0 0 10px rgba(0,255,0,0.3); }
        .option-card input { width: 100%; padding: 12px; margin: 10px 0; background: rgba(0,255,0,0.05); border: 1px solid rgba(0,255,0,0.3); border-radius: 10px; color: #00ff00; font-size: 14px; }
        .option-card input:focus { outline: none; border-color: #00ff00; }
        .option-card input::placeholder { color: rgba(0,255,0,0.3); }
        .option-card button { width: 100%; padding: 12px; background: linear-gradient(135deg, #00ff00, #009900); border: none; border-radius: 10px; color: #0a0a0a; font-weight: bold; cursor: pointer; font-size: 14px; }
        .result-box { background: rgba(0,0,0,0.5); border-radius: 15px; padding: 20px; margin-top: 20px; border: 1px solid rgba(0,255,0,0.2); max-height: 400px; overflow-y: auto; }
        .result-box p { color: #00ff00; margin: 5px 0; font-size: 13px; line-height: 1.8; }
        .result-box .label { color: rgba(0,255,0,0.6); }
        .result-box .value { color: #00ff00; font-weight: bold; }
        .result-box .error { color: #ff3366; }
        .map-container { margin-top: 20px; border-radius: 15px; overflow: hidden; border: 1px solid rgba(0,255,0,0.3); height: 300px; }
        .map-container iframe { width: 100%; height: 100%; border: none; }
        .protected { color: #ff6600; font-size: 18px; text-align: center; padding: 20px; }
        .footer { text-align: center; margin-top: 30px; font-size: 10px; color: rgba(0,255,0,0.3); padding: 20px; border-top: 1px solid rgba(0,255,0,0.1); }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>{{ fancy_title }}</h1>
        <div class="nav-links">
            <a href="/logout">LOGOUT</a>
        </div>
    </div>
    <div class="container">
        <div class="options">
            <!-- Number to Info -->
            <div class="option-card">
                <h2>NUM TO INFO</h2>
                <form method="POST" action="/num-info">
                    <input type="text" name="number" placeholder="ENTER MOBILE NUMBER" required>
                    <button type="submit">SEARCH</button>
                </form>
                {% if num_result %}
                <div class="result-box">
                    {% if num_result.protected %}
                    <div class="protected">⚠️ THIS NUMBER IS PROTECTED</div>
                    {% elif num_result.error %}
                    <p class="error">{{ num_result.error }}</p>
                    {% else %}
                    {% for item in num_result.data %}
                    <p><span class="label">NAME</span> : <span class="value">{{ item.Name or 'N/A' }}</span></p>
                    <p><span class="label">FATHER</span> : <span class="value">{{ item['Father Name'] or 'N/A' }}</span></p>
                    <p><span class="label">MOBILE</span> : <span class="value">{{ item.Mobile or 'N/A' }}</span></p>
                    <p><span class="label">ALT MOBILE</span> : <span class="value">{{ item['Alt Mobile'] or 'N/A' }}</span></p>
                    <p><span class="label">EMAIL</span> : <span class="value">{{ item.Email or 'N/A' }}</span></p>
                    <p><span class="label">ID</span> : <span class="value">{{ item.ID or 'N/A' }}</span></p>
                    <p><span class="label">CIRCLE</span> : <span class="value">{{ item.Circle or 'N/A' }}</span></p>
                    <p><span class="label">ADDRESS</span> : <span class="value">{{ item.Address or 'N/A' }}</span></p>
                    {% if item.lat and item.lon %}
                    <div class="map-container">
                        <iframe src="https://maps.google.com/maps?q={{ item.lat }},{{ item.lon }}&z=15&output=embed"></iframe>
                    </div>
                    {% endif %}
                    {% endfor %}
                    {% endif %}
                </div>
                {% endif %}
            </div>

            <!-- TG to Num -->
            <div class="option-card">
                <h2>TG TO NUM</h2>
                <form method="POST" action="/tg-info">
                    <input type="text" name="user_id" placeholder="ENTER TELEGRAM USER ID" required>
                    <button type="submit">SEARCH</button>
                </form>
                {% if tg_result %}
                <div class="result-box">
                    {% if tg_result.protected %}
                    <div class="protected">⚠️ THIS USER IS PROTECTED</div>
                    {% elif tg_result.error %}
                    <p class="error">{{ tg_result.error }}</p>
                    {% else %}
                    <p><span class="label">STATUS</span> : <span class="value">{{ tg_result.status or 'N/A' }}</span></p>
                    <p><span class="label">USERNAME</span> : <span class="value">{{ tg_result.username or 'N/A' }}</span></p>
                    <p><span class="label">MOBILE</span> : <span class="value">{{ tg_result.mobile or 'N/A' }}</span></p>
                    <p><span class="label">NAME</span> : <span class="value">{{ tg_result.name or 'N/A' }}</span></p>
                    {% if tg_result.lat and tg_result.lon %}
                    <div class="map-container">
                        <iframe src="https://maps.google.com/maps?q={{ tg_result.lat }},{{ tg_result.lon }}&z=15&output=embed"></iframe>
                    </div>
                    {% endif %}
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>
        <div class="footer">{{ fancy_dev }}</div>
    </div>
</body>
</html>
"""

ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Admin Login | BRIGHT X INFO</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}
body{min-height:100vh;background:#0a0a0a;display:flex;justify-content:center;align-items:center;}
.card{background:rgba(0,0,0,0.95);border-radius:30px;padding:40px;width:100%;max-width:400px;border:1px solid #00ff00;}
h2{color:#00ff00;text-align:center;margin-bottom:30px;font-size:24px;letter-spacing:2px;}
input{width:100%;padding:15px;margin:10px 0;background:rgba(0,255,0,0.05);border:1px solid rgba(0,255,0,0.3);border-radius:15px;color:#00ff00;font-size:14px;}
input:focus{outline:none;border-color:#00ff00;}
button{width:100%;padding:15px;background:linear-gradient(135deg,#00ff00,#009900);border:none;border-radius:15px;color:#0a0a2a;font-weight:bold;cursor:pointer;}
.error{color:#ff3366;text-align:center;margin-bottom:15px;}
</style>
</head>
<body>
<div class="card">
<h2>ADMIN LOGIN</h2>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="POST" action="/admin-login">
<input type="text" name="username" placeholder="USERNAME" required>
<input type="password" name="password" placeholder="PASSWORD" required>
<button type="submit">LOGIN</button>
</form>
</div>
</body>
</html>
"""

ADMIN_PANEL_HTML = """
<!DOCTYPE html>
<html>
<head><title>Admin Panel | BRIGHT X INFO</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Orbitron',monospace;}
body{background:#0a0a0a;min-height:100vh;}
.navbar{background:rgba(0,0,0,0.95);padding:15px 30px;display:flex;justify-content:space-between;border-bottom:1px solid #00ff00;}
.navbar h1{color:#00ff00;font-size:20px;}
.container{padding:30px;max-width:1400px;margin:0 auto;}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px;}
.stat-card{background:rgba(0,0,0,0.8);border:1px solid #00ff00;border-radius:20px;padding:25px;text-align:center;}
.stat-card h3{color:rgba(0,255,0,0.6);font-size:11px;}
.stat-card .value{color:#00ff00;font-size:28px;font-weight:bold;}
.section{background:rgba(0,0,0,0.8);border-radius:20px;padding:25px;margin-bottom:30px;border:1px solid rgba(0,255,0,0.3);}
.section h2{color:#00ff00;margin-bottom:20px;font-size:18px;}
table{width:100%;border-collapse:collapse;}
th,td{padding:12px;color:white;border-bottom:1px solid rgba(0,255,0,0.1);font-size:12px;}
th{color:#00ff00;}
.ban-btn{background:#ff3366;border:none;padding:5px 10px;border-radius:5px;color:white;cursor:pointer;}
.unban-btn{background:#00cc66;border:none;padding:5px 10px;border-radius:5px;color:white;cursor:pointer;}
</style>
</head>
<body>
<div class="navbar"><h1>ADMIN PANEL</h1><a href="/logout" style="color:#00ff00;">LOGOUT</a></div>
<div class="container">
<div class="stats">
<div class="stat-card"><h3>TOTAL USERS</h3><div class="value">{{ users|length }}</div></div>
<div class="stat-card"><h3>BANNED</h3><div class="value">{{ banned_count }}</div></div>
</div>

<div class="section"><h2>USERS</h2>
<div class="table-container">
<table><thead><tr><th>ID</th><th>USERNAME</th><th>USER ID</th><th>IP</th><th>STATUS</th><th>ACTION</th></tr></thead>
<tbody>
{% for u in users %}
<tr>
<td>{{ u.id }}</td>
<td>{{ u.username or '-' }}</td>
<td>{{ u.user_id }}</td>
<td>{{ u.ip_address or '-' }}</td>
<td style="color:{% if u.is_banned %}#ff3366{% else %}#00ff00{% endif %};">{{ 'BANNED' if u.is_banned else 'ACTIVE' }}</td>
<td>
{% if u.is_banned %}
<form method="POST" action="/admin/unban" style="display:inline;">
<input type="hidden" name="user_id" value="{{ u.user_id }}">
<button type="submit" class="unban-btn">UNBAN</button>
</form>
{% else %}
<form method="POST" action="/admin/ban" style="display:inline;">
<input type="hidden" name="user_id" value="{{ u.user_id }}">
<button type="submit" class="ban-btn">BAN</button>
</form>
{% endif %}
</td>
</tr>
{% endfor %}
</tbody></table></div></div>
</div>
</body>
</html>
"""

# ============ FLASK ROUTES ============
@app.route('/')
def index():
    if 'access_granted' in session:
        return redirect('/dashboard')
    fancy_title = to_fancy("BRIGHT X INFO")
    return render_template_string(KEY_PAGE_HTML, fancy_title=fancy_title)

@app.route('/verify-key', methods=['POST'])
def verify_key():
    key = request.form.get('key')
    if key == WEB_ACCESS_KEY:
        session['access_granted'] = True
        return redirect('/dashboard')
    fancy_title = to_fancy("BRIGHT X INFO")
    return render_template_string(KEY_PAGE_HTML, fancy_title=fancy_title, error="INVALID ACCESS KEY!")

@app.route('/dashboard')
def dashboard():
    if 'access_granted' not in session:
        return redirect('/')
    fancy_title = to_fancy("BRIGHT X INFO")
    fancy_dev = to_fancy("Developer: @iflexvenom")
    return render_template_string(DASHBOARD_HTML, fancy_title=fancy_title, fancy_dev=fancy_dev)

@app.route('/num-info', methods=['POST'])
def num_info():
    if 'access_granted' not in session:
        return redirect('/')
    
    number = request.form.get('number')
    result = get_num_info(number)
    fancy_title = to_fancy("BRIGHT X INFO")
    fancy_dev = to_fancy("Developer: @iflexvenom")
    
    if result.get('status'):
        # Extract address for map
        data = result.get('data', [])
        if data and isinstance(data, list) and len(data) > 0:
            addr = data[0].get('Address', '')
            # Try to geocode or use placeholder
            # For map, we'll use a generic location if no lat/lon
            pass
        return render_template_string(DASHBOARD_HTML, fancy_title=fancy_title, fancy_dev=fancy_dev, num_result=result)
    else:
        return render_template_string(DASHBOARD_HTML, fancy_title=fancy_title, fancy_dev=fancy_dev, num_result={"error": "Number not found or API error"})

@app.route('/tg-info', methods=['POST'])
def tg_info():
    if 'access_granted' not in session:
        return redirect('/')
    
    user_id = request.form.get('user_id')
    result = get_tg_info(user_id)
    fancy_title = to_fancy("BRIGHT X INFO")
    fancy_dev = to_fancy("Developer: @iflexvenom")
    
    if result.get('status'):
        return render_template_string(DASHBOARD_HTML, fancy_title=fancy_title, fancy_dev=fancy_dev, tg_result=result)
    else:
        return render_template_string(DASHBOARD_HTML, fancy_title=fancy_title, fancy_dev=fancy_dev, tg_result={"error": "User not found or API error"})

# ============ ADMIN ROUTES ============
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin_logged_in'] = True
            return redirect('/admin')
        return render_template_string(ADMIN_LOGIN_HTML, error="Invalid credentials!")
    return render_template_string(ADMIN_LOGIN_HTML)

@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect('/admin-login')
    
    users = User.query.all()
    banned_count = User.query.filter_by(is_banned=True).count()
    return render_template_string(ADMIN_PANEL_HTML, users=users, banned_count=banned_count)

@app.route('/admin/ban', methods=['POST'])
def admin_ban():
    if not session.get('admin_logged_in'):
        return redirect('/admin-login')
    
    user_id = request.form.get('user_id')
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        user.is_banned = True
        db.session.commit()
    return redirect('/admin')

@app.route('/admin/unban', methods=['POST'])
def admin_unban():
    if not session.get('admin_logged_in'):
        return redirect('/admin-login')
    
    user_id = request.form.get('user_id')
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        user.is_banned = False
        db.session.commit()
    return redirect('/admin')

@app.route('/health')
def health():
    return "OK", 200

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)