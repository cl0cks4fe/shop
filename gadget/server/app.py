from flask import Flask, request, render_template, redirect, url_for, request
import os
import subprocess
import time
import threading
import logging
import requests

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
DIRECTOR_URL = 'http://192.168.0.118:5000'

registered = False

app = Flask(__name__)
logger = logging.getLogger(__name__)

class LogHandler(logging.Handler):
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def emit(self, record):
        log_entry = self.format(record)
        if registered:
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

def register():
    global registered
    while True:
        if not registered:
            logger.info(f"attempting to register ({DIRECTOR_URL})...")
            try: 
                response = requests.post(f'{DIRECTOR_URL}/register', json={'id': DEVICE_NAME})

                if response.status_code == 201:
                    registered = True
            except:
                logger.error("attempt to register failed")
        else:
            try: 
                response = requests.post(f'{DIRECTOR_URL}/register', json={'id': DEVICE_NAME})

                if response.status_code != 200:
                    registered = False
            except:
                logger.error("can't reach director")
    
        time.sleep(5)

if __name__ == '__main__':
    log_handler = LogHandler(f'{DIRECTOR_URL}/logs')
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.ERROR)

    register_thread = threading.Thread(target=register, daemon=True)
    register_thread.start()

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=8080)
