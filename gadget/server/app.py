from flask import Flask, request, render_template, redirect, url_for
import os
import subprocess
import time
import threading
import logging
import requests

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
DIRECTOR_URL = os.environ.get('DIRECTOR_URL', 'http://192.168.0.118:3000')

# Thread-safe connection flag
connected_flag = threading.Event()

app = Flask(__name__)
logger = logging.getLogger(__name__)

class LogHandler(logging.Handler):
    def __init__(self, url):
        super().__init__()
        self.url = url
    def emit(self, record):
        log_entry = self.format(record)
        if connected_flag.is_set():
            try:
                requests.post(self.url, json={"log": log_entry}, timeout=2)
            except Exception:
                print(log_entry)
        else:
            print(log_entry)

def get_device_name():
    try:
        with open('/etc/gadget-device-name', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return 'unknown'

DEVICE_NAME = get_device_name()

def allowed_file(filename):
    return True

def secure_filename(filename):
    return os.path.basename(filename)

@app.route('/ping', methods=['GET'])
def ping():
    return 'ok', 200

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file selected', 400
        file = request.files['file']
        filename = secure_filename(file.filename)
        if filename == '' or not allowed_file(filename):
            return 'Invalid file type', 400
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        try:
            file.save(filepath)
        except Exception as e:
            logger.error(f"File save failed: {e}")
            return 'File save failed', 500
        try:
            subprocess.run([os.path.join(os.getcwd(), 'scripts/transfer.sh')], check=True)
            return redirect(url_for('upload', success=True))
        except subprocess.CalledProcessError:
            logger.error("Update failed during transfer.sh execution")
            return 'Update failed', 500
    success = request.args.get('success')
    return render_template('index.html', success=success, device_name=DEVICE_NAME)

def ping_loop():
    while True:
        try:
            response = requests.get(f'{DIRECTOR_URL}/ping', headers={'id': f'{DEVICE_NAME}'}, timeout=2)
            if response.status_code == 200:
                connected_flag.set()
            else:
                connected_flag.clear()
        except Exception:
            connected_flag.clear()
        time.sleep(5)

if __name__ == '__main__':
    log_handler = LogHandler(f'{DIRECTOR_URL}/logs')
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.ERROR)
    ping_thread = threading.Thread(target=ping_loop, daemon=True)
    ping_thread.start()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=3000)
