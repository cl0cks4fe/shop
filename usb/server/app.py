import os, shutil, subprocess, threading, time, logging
from pathlib import Path
from flask import Flask, request, render_template, jsonify, redirect, url_for

DEV_MODE = os.environ.get('DEV', '').lower() in ('1', 'true', 'yes', 'on')

UPLOAD_DIR = Path('upload')
TRANSFER_DIR = Path('transferred') if DEV_MODE else None

TRANSFER_SCRIPT = Path(__file__).parent / 'scripts' / 'transfer.sh'


def _device_name():
    if DEV_MODE:
        return 'dev'
    try:
        return Path('/etc/gadget-device-name').read_text().strip()
    except FileNotFoundError:
        return 'unknown'


DEVICE_NAME = _device_name()
_active = None
_lock = threading.Lock()
log = logging.getLogger(__name__)

app = Flask(__name__)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
if TRANSFER_DIR: TRANSFER_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/status')
def status():
    info = {'device_name': DEVICE_NAME}
    with _lock:
        if _active:
            info['active_transfer'] = _active
    return jsonify(info)


@app.route('/')
def index():
    return redirect(url_for('upload'))


@app.route('/upload')
def upload():
    return render_template('upload.html', device_name=DEVICE_NAME)


def _transfer(filename):
    global _active
    try:
        if DEV_MODE:
            time.sleep(2)
            shutil.copy2(UPLOAD_DIR / filename, TRANSFER_DIR / filename)
            (UPLOAD_DIR / filename).unlink()
        else:
            subprocess.run([str(TRANSFER_SCRIPT)], check=True, timeout=120)
        log.info(f'Transfer complete: {filename}')
    except Exception as e:
        log.error(f'Transfer failed: {e}')
    finally:
        with _lock:
            _active = None


@app.route('/upload', methods=['POST'])
def upload_file():
    global _active

    with _lock:
        if _active:
            return jsonify({'error': f'"{_active}" is transferring, please wait'}), 409

    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': 'No file provided'}), 400

    filename = os.path.basename(file.filename)
    file.save(UPLOAD_DIR / filename)

    with _lock:
        _active = filename

    threading.Thread(target=_transfer, args=(filename,)).start()
    return jsonify({'filename': filename}), 202


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
