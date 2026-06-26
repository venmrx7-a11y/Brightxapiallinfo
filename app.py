from flask import Flask, render_template_string, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
import json
import hashlib
import re

app = Flask(__name__)
app.secret_key = "bright_x_info_secret_2024"

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
    user_id = db.Column(db.String(100), unique=True, nullable=False)
    display_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned = db.Column(db.Boolean, default=False)
    search_history = db.Column(db.Text, nullable=True)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_super = db.Column(db.Boolean, default=False)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

class UserSearch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    search_type = db.Column(db.String(20), nullable=False)
    query = db.Column(db.String(100), nullable=False)
    result = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()
    
    admin = Admin.query.filter_by(username="VENOM-X-OWNER").first()
    if not admin:
        admin = Admin(username="VENOM-X-OWNER", password="VENOM-X-OWNER", is_super=True)
        db.session.add(admin)
        db.session.commit()
    
    if not Setting.query.filter_by(key='bg_image').first():
        setting = Setting(key='bg_image', value='')
        db.session.add(setting)
    if not Setting.query.filter_by(key='primary_color').first():
        setting = Setting(key='primary_color', value='#00ff00')
        db.session.add(setting)
    db.session.commit()

# ============ STYLISH TEXT ============
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

# ============ HELPERS ============
def get_setting(key):
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else None

def set_setting(key, value):
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    db.session.commit()

def get_next_display_id():
    last_user = User.query.order_by(User.display_id.desc()).first()
    if last_user:
        return last_user.display_id + 1
    return 18277

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

def extract_numbers(data):
    """Extract all phone numbers from data"""
    numbers = set()
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and re.match(r'^\+?\d{10,15}$', value):
                numbers.add(value)
            elif isinstance(value, (dict, list)):
                numbers.update(extract_numbers(value))
    elif isinstance(data, list):
        for item in data:
            numbers.update(extract_numbers(item))
    return numbers

def get_all_alternatives(number, max_depth=3):
    """Recursively get all alternative numbers"""
    all_numbers = set()
    all_numbers.add(number)
    
    result = get_num_info(number)
    if not result.get('status'):
        return all_numbers, result
    
    data = result.get('data', [])
    if data and isinstance(data, list) and len(data) > 0:
        alt_mobile = data[0].get('Alt Mobile', '')
        if alt_mobile and alt_mobile != 'N/A' and alt_mobile != number:
            all_numbers.add(alt_mobile)
            # Recursively search alternative
            if max_depth > 0:
                alt_result = get_all_alternatives(alt_mobile, max_depth-1)
                all_numbers.update(alt_result[0])
    
    return all_numbers, result

def register_user(user_id, username=None, ip=None):
    user = User.query.filter_by(user_id=str(user_id)).first()
    if not user:
        display_id = get_next_display_id()
        user = User(user_id=str(user_id), username=username, ip_address=ip, display_id=display_id)
        db.session.add(user)
        db.session.commit()
        # Send notification to Telegram bot (if configured)
        try:
            send_telegram_notification(f"🔔 NEW USER JOINED!\nID: {display_id}\nUser: {user_id}\nIP: {ip or 'N/A'}")
        except:
            pass
    return user

def is_banned(user_id):
    user = User.query.filter_by(user_id=str(user_id)).first()
    return user and user.is_banned

def send_telegram_notification(message):
    # Placeholder - tu yahan apna bot token daal sakta hai
    try:
        # Optional: Send to Telegram bot
        pass
    except:
        pass

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
        body::before { content: ''; position: absolute; width: 100%; height: 100%; background: {{ bg_style }}; background-size: cover; background-position: center; opacity: 0.3; z-index: 0; }
        .glow { position: absolute; width: 300px; height: 300px; background: radial-gradient(circle, {{ primary_color }}22 0%, transparent 70%); border-radius: 50%; animation: pulse 3s ease-in-out infinite; z-index: 0; }
        @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 0.3; } 50% { transform: scale(1.5); opacity: 0.1; } }
        .glow:nth-child(1) { top: -100px; left: -100px; animation-delay: 0s; }
        .glow:nth-child(2) { bottom: -100px; right: -100px; animation-delay: 1.5s; }
        .card { position: relative; z-index: 1; background: rgba(0,0,0,0.9); backdrop-filter: blur(10px); border-radius: 30px; padding: 50px 40px; width: 100%; max-width: 450px; border: 1px solid {{ primary_color }}66; box-shadow: 0 0 50px {{ primary_color }}22; }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { font-size: 28px; font-weight: 800; letter-spacing: 4px; color: {{ primary_color }}; text-shadow: 0 0 20px {{ primary_color }}55; }
        .logo p { color: {{ primary_color }}88; font-size: 11px; letter-spacing: 3px; margin-top: 5px; }
        .sub { color: {{ primary_color }}88; text-align: center; font-size: 12px; margin-bottom: 30px; letter-spacing: 2px; }
        .input-group { margin-bottom: 22px; }
        .input-group input { width: 100%; padding: 15px 20px; background: rgba(0,0,0,0.5); border: 1px solid {{ primary_color }}44; border-radius: 15px; color: {{ primary_color }}; font-size: 14px; letter-spacing: 1px; }
        .input-group input:focus { outline: none; border-color: {{ primary_color }}; box-shadow: 0 0 30px {{ primary_color }}33; }
        .input-group input::placeholder { color: {{ primary_color }}44; }
        .btn { width: 100%; padding: 15px; background: linear-gradient(135deg, {{ primary_color }}, {{ primary_color }}88); border: none; border-radius: 15px; color: #0a0a0a; font-size: 16px; font-weight: 800; letter-spacing: 2px; cursor: pointer; transition: 0.3s; }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 8px 30px {{ primary_color }}55; }
        .error { background: rgba(255,0,0,0.2); border: 1px solid #ff0000; border-radius: 12px; padding: 12px; margin-bottom: 20px; text-align: center; color: #ff6666; font-size: 12px; }
        .footer { text-align: center; margin-top: 30px; font-size: 9px; color: {{ primary_color }}44; }
        .admin-link { color: {{ primary_color }}44; text-decoration: none; font-size: 10px; display: block; margin-top: 15px; }
        .admin-link:hover { color: {{ primary_color }}; }
    </style>
</head>
<body>
    <div class="glow"></div>
    <div class="glow"></div>
    <div class="card">
        <div class="logo">
            <h1>BRIGHT X INFO</h1>
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
        .navbar { background: rgba(0,0,0,0.95); padding: 12px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid {{ primary_color }}; flex-wrap: wrap; gap: 10px; }
        .navbar h1 { font-size: 18px; letter-spacing: 2px; color: {{ primary_color }}; text-shadow: 0 0 20px {{ primary_color }}33; }
        .nav-right { display: flex; align-items: center; gap: 15px; }
        .nav-right .wallet { color: {{ primary_color }}; font-size: 12px; }
        .menu-btn { background: none; border: none; cursor: pointer; display: flex; flex-direction: column; gap: 4px; padding: 5px; }
        .menu-btn span { width: 22px; height: 2px; background: {{ primary_color }}; transition: 0.3s; }
        .sidebar { position: fixed; top: 0; right: -280px; width: 280px; height: 100%; background: rgba(0,0,0,0.98); border-left: 1px solid {{ primary_color }}; padding: 80px 20px 20px; transition: 0.3s; z-index: 200; }
        .sidebar.active { right: 0; }
        .sidebar a { display: block; color: white; text-decoration: none; padding: 15px; margin: 8px 0; border-radius: 10px; font-size: 13px; letter-spacing: 1px; }
        .sidebar a:hover { background: rgba(0,255,0,0.1); color: {{ primary_color }}; }
        .close-sidebar { position: absolute; top: 20px; right: 20px; font-size: 24px; cursor: pointer; color: {{ primary_color }}; }
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: none; z-index: 150; }
        .container { padding: 25px; max-width: 1400px; margin: 0 auto; }
        .user-info { color: {{ primary_color }}88; font-size: 12px; margin-bottom: 20px; text-align: right; }
        .options { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
        @media(max-width:768px){ .options { grid-template-columns: 1fr; } }
        .option-card { background: rgba(0,0,0,0.85); border-radius: 20px; padding: 25px; border: 1px solid {{ primary_color }}44; }
        .option-card h2 { color: {{ primary_color }}; font-size: 16px; margin-bottom: 15px; letter-spacing: 2px; text-shadow: 0 0 15px {{ primary_color }}22; }
        .option-card input { width: 100%; padding: 12px; margin: 8px 0; background: rgba(0,0,0,0.5); border: 1px solid {{ primary_color }}33; border-radius: 10px; color: {{ primary_color }}; font-size: 13px; }
        .option-card input:focus { outline: none; border-color: {{ primary_color }}; }
        .option-card input::placeholder { color: {{ primary_color }}44; }
        .option-card button { width: 100%; padding: 12px; background: linear-gradient(135deg, {{ primary_color }}, {{ primary_color }}88); border: none; border-radius: 10px; color: #0a0a0a; font-weight: bold; cursor: pointer; font-size: 13px; }
        .result-box { background: rgba(0,0,0,0.6); border-radius: 15px; padding: 15px; margin-top: 15px; border: 1px solid {{ primary_color }}22; max-height: 450px; overflow-y: auto; }
        .result-box .label { color: {{ primary_color }}66; font-size: 11px; }
        .result-box .value { color: {{ primary_color }}; font-weight: bold; font-size: 12px; }
        .result-box .detail-row { padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .result-box .section-title { color: {{ primary_color }}88; font-size: 13px; margin-top: 15px; margin-bottom: 10px; border-bottom: 1px solid {{ primary_color }}33; padding-bottom: 5px; }
        .result-box .error { color: #ff3366; }
        .result-box .protected { color: #ff6600; font-size: 16px; text-align: center; padding: 15px; }
        .copy-btn { background: rgba(255,255,255,0.1); border: 1px solid {{ primary_color }}44; padding: 5px 12px; border-radius: 6px; color: {{ primary_color }}; cursor: pointer; font-size: 10px; margin-bottom: 10px; }
        .copy-btn:hover { background: rgba(0,255,0,0.1); }
        .raw-btn { background: rgba(255,255,255,0.05); border: 1px solid {{ primary_color }}33; padding: 5px 12px; border-radius: 6px; color: {{ primary_color }}88; cursor: pointer; font-size: 10px; margin-right: 10px; }
        .raw-btn:hover { background: rgba(0,255,0,0.05); }
        .map-container { margin-top: 15px; border-radius: 12px; overflow: hidden; border: 1px solid {{ primary_color }}33; height: 200px; }
        .map-container iframe { width: 100%; height: 100%; border: none; }
        .footer { text-align: center; margin-top: 30px; font-size: 10px; color: {{ primary_color }}33; padding: 15px; border-top: 1px solid rgba(0,255,0,0.05); }
        .badge { background: {{ primary_color }}22; padding: 2px 10px; border-radius: 20px; font-size: 10px; color: {{ primary_color }}; display: inline-block; margin-top: 5px; }
        .notification-dot { width: 8px; height: 8px; background: #ff3366; border-radius: 50%; display: inline-block; margin-left: 5px; animation: blink 1s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        .my-details-card { background: rgba(0,0,0,0.85); border-radius: 20px; padding: 20px; border: 1px solid {{ primary_color }}44; margin-top: 20px; }
        .my-details-card h3 { color: {{ primary_color }}; font-size: 14px; letter-spacing: 2px; margin-bottom: 15px; }
        .my-details-card .detail-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .my-details-card .detail-item .label { color: {{ primary_color }}66; font-size: 12px; }
        .my-details-card .detail-item .value { color: {{ primary_color }}; font-size: 12px; }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>BRIGHT X INFO</h1>
        <div class="nav-right">
            <span class="wallet">ID: {{ user_display_id }}</span>
            <button class="menu-btn" onclick="toggleSidebar()">
                <span></span><span></span><span></span>
            </button>
        </div>
    </div>

    <div class="sidebar" id="sidebar">
        <div class="close-sidebar" onclick="toggleSidebar()">✕</div>
        <a href="#" onclick="showNotifications()">🔔 NOTIFICATIONS</a>
        <a href="#" onclick="showMyDetails()">👤 MY DETAILS</a>
        <a href="/logout">🚪 LOGOUT</a>
    </div>
    <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>

    <div class="container">
        <div class="user-info">{{ user_display_name or 'GUEST' }}</div>

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
                    <button class="raw-btn" onclick="toggleRaw('numRaw')">RAW DATA</button>
                    <button class="copy-btn" onclick="copyResult('numResult')">📋 COPY</button>
                    <div id="numResult">
                    {% if num_result.protected %}
                    <div class="protected">⚠️ THIS NUMBER IS PROTECTED</div>
                    {% elif num_result.error %}
                    <p class="error">{{ num_result.error }}</p>
                    {% else %}
                    {% set all_data = num_result.all_data %}
                    {% for item in all_data %}
                    <div class="detail-row">
                        <span class="label">NAME</span> : <span class="value">{{ item.Name or 'N/A' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">FATHER</span> : <span class="value">{{ item['Father Name'] or 'N/A' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">MOBILE</span> : <span class="value">{{ item.Mobile or 'N/A' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">ALT MOBILE</span> : <span class="value">{{ item['Alt Mobile'] or 'N/A' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">EMAIL</span> : <span class="value">{{ item.Email or 'N/A' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">AADHAR</span> : <span class="value">{{ item.ID or 'N/A' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">CIRCLE</span> : <span class="value">{{ item.Circle or 'N/A' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">ADDRESS</span> : <span class="value">{{ item.Address or 'N/A' }}</span>
                    </div>
                    {% endfor %}
                    <div class="section-title">ALTERNATIVE NUMBERS</div>
                    {% if num_result.all_numbers %}
                    {% for num in num_result.all_numbers %}
                    <div class="detail-row">
                        <span class="label">NUMBER</span> : <span class="value">{{ num }}</span>
                    </div>
                    {% endfor %}
                    {% else %}
                    <div class="detail-row"><span class="label">No alternative numbers found</span></div>
                    {% endif %}
                    <div class="section-title">LOCATION</div>
                    <div class="map-container">
                        <iframe src="https://maps.google.com/maps?q=28.6139,77.2090&z=12&output=embed"></iframe>
                    </div>
                    {% endif %}
                    </div>
                    <div id="numRaw" style="display:none; margin-top:10px;">
                        <pre style="color:#00ff00; font-size:10px; white-space:pre-wrap; word-wrap:break-word;">{{ num_result.raw|tojson|safe }}</pre>
                    </div>
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
                    <button class="raw-btn" onclick="toggleRaw('tgRaw')">RAW DATA</button>
                    <button class="copy-btn" onclick="copyResult('tgResult')">📋 COPY</button>
                    <div id="tgResult">
                    {% if tg_result.protected %}
                    <div class="protected">⚠️ THIS USER IS PROTECTED</div>
                    {% elif tg_result.error %}
                    <p class="error">{{ tg_result.error }}</p>
                    {% else %}
                    <div class="detail-row">
                        <span class="label">USERNAME</span> : <span class="value">{{ tg_result.username or 'N/A' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">NAME</span> : <span class="value">{{ tg_result.name or 'N/A' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">MOBILE</span> : <span class="value">{{ tg_result.mobile or 'N/A' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">STATUS</span> : <span class="value">{{ tg_result.status or 'N/A' }}</span>
                    </div>
                    <div class="section-title">ALTERNATIVE NUMBERS</div>
                    {% if tg_result.all_numbers %}
                    {% for num in tg_result.all_numbers %}
                    <div class="detail-row">
                        <span class="label">NUMBER</span> : <span class="value">{{ num }}</span>
                    </div>
                    {% endfor %}
                    {% else %}
                    <div class="detail-row"><span class="label">No alternative numbers found</span></div>
                    {% endif %}
                    <div class="section-title">LOCATION</div>
                    <div class="map-container">
                        <iframe src="https://maps.google.com/maps?q=28.6139,77.2090&z=12&output=embed"></iframe>
                    </div>
                    {% endif %}
                    </div>
                    <div id="tgRaw" style="display:none; margin-top:10px;">
                        <pre style="color:#00ff00; font-size:10px; white-space:pre-wrap; word-wrap:break-word;">{{ tg_result.raw|tojson|safe }}</pre>
                    </div>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- My Details -->
        <div class="my-details-card" id="myDetailsCard" style="display:none;">
            <h3>👤 MY DETAILS</h3>
            <div class="detail-item"><span class="label">USER ID</span><span class="value">{{ user_display_id }}</span></div>
            <div class="detail-item"><span class="label">TELEGRAM ID</span><span class="value">{{ user_id }}</span></div>
            <div class="detail-item"><span class="label">USERNAME</span><span class="value">{{ user_username or 'Not set' }}</span></div>
            <div class="detail-item"><span class="label">IP ADDRESS</span><span class="value">{{ user_ip or 'N/A' }}</span></div>
            <div class="detail-item"><span class="label">FIRST SEEN</span><span class="value">{{ user_first_seen or 'N/A' }}</span></div>
            <div class="detail-item"><span class="label">STATUS</span><span class="value" style="color:{% if not user_banned %}#00ff00{% else %}#ff3366{% endif %};">{{ 'ACTIVE' if not user_banned else 'BANNED' }}</span></div>
            <div class="badge">Developer: @iflexvenom</div>
        </div>

        <div class="footer">Developer: @iflexvenom</div>
    </div>

    <script>
        function toggleSidebar() {
            var s = document.getElementById('sidebar');
            var o = document.getElementById('overlay');
            s.classList.toggle('active');
            o.style.display = s.classList.contains('active') ? 'block' : 'none';
        }

        function toggleRaw(id) {
            var el = document.getElementById(id);
            if (el.style.display === 'none') {
                el.style.display = 'block';
            } else {
                el.style.display = 'none';
            }
        }

        function copyResult(id) {
            var el = document.getElementById(id);
            var text = el.innerText;
            navigator.clipboard.writeText(text).then(function() {
                alert('📋 Copied to clipboard!');
            }).catch(function() {
                alert('Could not copy. Select text manually.');
            });
        }

        function showNotifications() {
            alert('🔔 No new notifications.');
        }

        function showMyDetails() {
            var card = document.getElementById('myDetailsCard');
            if (card.style.display === 'none') {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
            toggleSidebar();
        }
    </script>
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
.section h3{color:#00ff00;margin-top:15px;font-size:14px;}
.section input{width:100%;padding:12px;margin:5px 0;background:rgba(0,255,0,0.05);border:1px solid rgba(0,255,0,0.3);border-radius:10px;color:#00ff00;}
.section button{background:linear-gradient(135deg,#00ff00,#009900);border:none;padding:10px 20px;border-radius:10px;color:#0a0a0a;font-weight:bold;cursor:pointer;}
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

<div class="section"><h2>⚙️ SETTINGS</h2>
<form method="POST" action="/admin/update-settings">
<div><label style="color:#aaa;">Background Image URL</label><input type="text" name="bg_image" value="{{ settings.bg_image }}"></div>
<div><label style="color:#aaa;">Primary Color</label><input type="text" name="primary_color" value="{{ settings.primary_color }}"></div>
<button type="submit">UPDATE</button>
</form></div>

<div class="section"><h2>👥 USERS</h2>
<div class="table-container">
<table><thead><tr><th>ID</th><th>DISPLAY ID</th><th>USERNAME</th><th>USER ID</th><th>IP</th><th>STATUS</th><th>ACTION</th></tr></thead>
<tbody>
{% for u in users %}
<tr>
<td>{{ u.id }}</td>
<td>{{ u.display_id }}</td>
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
    bg_image = get_setting('bg_image')
    primary_color = get_setting('primary_color') or '#00ff00'
    bg_style = f"url('{bg_image}')" if bg_image else "#0a0a0a"
    return render_template_string(KEY_PAGE_HTML, bg_style=bg_style, primary_color=primary_color)

@app.route('/verify-key', methods=['POST'])
def verify_key():
    key = request.form.get('key')
    if key == WEB_ACCESS_KEY:
        session['access_granted'] = True
        return redirect('/dashboard')
    bg_image = get_setting('bg_image')
    primary_color = get_setting('primary_color') or '#00ff00'
    bg_style = f"url('{bg_image}')" if bg_image else "#0a0a0a"
    return render_template_string(KEY_PAGE_HTML, bg_style=bg_style, primary_color=primary_color, error="INVALID ACCESS KEY!")

@app.route('/dashboard')
def dashboard():
    if 'access_granted' not in session:
        return redirect('/')
    
    user_id = session.get('user_id', 'GUEST')
    user = User.query.filter_by(user_id=str(user_id)).first() if user_id != 'GUEST' else None
    
    primary_color = get_setting('primary_color') or '#00ff00'
    
    return render_template_string(DASHBOARD_HTML, 
                                   user_display_id=user.display_id if user else 'N/A',
                                   user_id=user_id,
                                   user_username=user.username if user else 'N/A',
                                   user_ip=user.ip_address if user else 'N/A',
                                   user_first_seen=user.first_seen.strftime('%Y-%m-%d %H:%M') if user else 'N/A',
                                   user_banned=user.is_banned if user else False,
                                   primary_color=primary_color,
                                   user_display_name=user.username if user else 'GUEST')

@app.route('/num-info', methods=['POST'])
def num_info():
    if 'access_granted' not in session:
        return redirect('/')
    
    number = request.form.get('number')
    primary_color = get_setting('primary_color') or '#00ff00'
    
    # Get all alternatives recursively
    all_numbers, result = get_all_alternatives(number)
    all_numbers = sorted(list(all_numbers), key=lambda x: len(x))
    
    num_result = {
        'data': result.get('data', []),
        'all_numbers': all_numbers,
        'raw': result,
        'protected': 'protected' in str(result).lower() if result else False
    }
    
    # Register user search
    user_id = session.get('user_id', 'UNKNOWN')
    search = UserSearch(user_id=user_id, search_type='num', query=number, result=json.dumps(result))
    db.session.add(search)
    db.session.commit()
    
    return render_template_string(DASHBOARD_HTML, 
                                   num_result=num_result,
                                   user_display_id='N/A',
                                   user_id=user_id,
                                   primary_color=primary_color,
                                   user_display_name='USER')

@app.route('/tg-info', methods=['POST'])
def tg_info():
    if 'access_granted' not in session:
        return redirect('/')
    
    tg_id = request.form.get('user_id')
    primary_color = get_setting('primary_color') or '#00ff00'
    
    result = get_tg_info(tg_id)
    
    all_numbers = set()
    if result.get('status'):
        # Extract numbers from response
        all_numbers = extract_numbers(result)
    
    tg_result = {
        'data': result.get('data', {}),
        'all_numbers': list(all_numbers) if all_numbers else [],
        'raw': result,
        'protected': 'protected' in str(result).lower() if result else False
    }
    
    # Register user search
    user_id = session.get('user_id', 'UNKNOWN')
    search = UserSearch(user_id=user_id, search_type='tg', query=tg_id, result=json.dumps(result))
    db.session.add(search)
    db.session.commit()
    
    return render_template_string(DASHBOARD_HTML, 
                                   tg_result=tg_result,
                                   user_display_id='N/A',
                                   user_id=user_id,
                                   primary_color=primary_color,
                                   user_display_name='USER')

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
    settings = {
        'bg_image': get_setting('bg_image') or '',
        'primary_color': get_setting('primary_color') or '#00ff00'
    }
    return render_template_string(ADMIN_PANEL_HTML, users=users, banned_count=banned_count, settings=settings)

@app.route('/admin/update-settings', methods=['POST'])
def update_settings():
    if not session.get('admin_logged_in'):
        return redirect('/admin-login')
    
    set_setting('bg_image', request.form.get('bg_image'))
    set_setting('primary_color', request.form.get('primary_color'))
    return redirect('/admin')

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
