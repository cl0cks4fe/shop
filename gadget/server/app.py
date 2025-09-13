from flask import Flask, request, render_template, redirect, url_for, request
import os
import subprocess
import time
import threading
import logging
import requests

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
DIRECTOR_URL = 'http://192.168.0.118:3000'

connected = False

app = Flask(__name__)
logger = logging.getLogger(__name__)

class LogHandler(logging.Handler):
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def emit(self, record):
        log_entry = self.format(record)
        if connected:
            requests.post(self.url, json={"log": log_entry})
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

@app.route('/ping', methods=['GET'])
def ping():
    return 'ok', 200

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file selected', 400

        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return 'Invalid file type', 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        try:
            subprocess.run([os.path.join(os.getcwd(), 'scripts/transfer.sh')], check=True)
            return redirect(url_for('upload', success=True))
        except subprocess.CalledProcessError:
            return 'Update failed', 500

    success = request.args.get('success')
    return render_template('index.html', success=success, device_name=DEVICE_NAME)

def ping():
    global connected

    while True:
        try:
            response = requests.get(f'{DIRECTOR_URL}/ping', headers={'id': f'{DEVICE_NAME}'})
            connected = True if response.status_code == 200 else False
        except:
            connected = False
        time.sleep(5)

if __name__ == '__main__':
    log_handler = LogHandler(f'{DIRECTOR_URL}/logs')
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.ERROR)

    ping_thread = threading.Thread(target=ping, daemon=True)
    ping_thread.start()

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=3000)
