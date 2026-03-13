import shutil, subprocess, time, threading
import logging
import os
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

api_bp = Blueprint('api', __name__, url_prefix='/api')

_active = None
_lock = threading.Lock()

log = logging.getLogger(__name__)

DEV_MODE = os.environ.get('DEV', '').lower() in ('1', 'true', 'yes', 'on')

TRANSFER_SCRIPT = Path(__file__).parent / 'scripts' / 'transfer.sh'
UPLOAD_DIR = Path('upload')
TRANSFER_DIR = Path('transferred') if DEV_MODE else None


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
if TRANSFER_DIR: TRANSFER_DIR.mkdir(parents=True, exist_ok=True)

if DEV_MODE:
    DEVICE_NAME = 'dev'
else:
    try:
        DEVICE_NAME = Path('/etc/gadget-device-name').read_text().strip()
    except FileNotFoundError:
        DEVICE_NAME = 'unknown'

@api_bp.route('/status')
def status():
    info = {'device_name': DEVICE_NAME}
    with _lock:
        if _active:
            info['active_transfer'] = _active
    return jsonify(info)


def _transfer(filename):
    global _active
    try:
        if DEV_MODE:
            time.sleep(2)
            upload_dir = UPLOAD_DIR
            transfer_dir = TRANSFER_DIR
            shutil.copy2(str(upload_dir / filename), str(transfer_dir / filename))
            (upload_dir / filename).unlink()
        else:
            subprocess.run([str(TRANSFER_SCRIPT)], check=True, timeout=120)
        log.info(f'Transfer complete: {filename}')
    except Exception as e:
        log.error(f'Transfer failed: {e}')
    finally:
        with _lock:
            _active = None


@api_bp.route('/upload', methods=['POST'])
def upload():
    global _active

    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': 'No file provided'}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({'error': 'Invalid filename'}), 400

    with _lock:
        if _active:
            return jsonify({'error': f'"{_active}" is transferring, please wait'}), 409
        _active = filename

    upload_dir = UPLOAD_DIR
    file.save(str(upload_dir / filename))
    threading.Thread(target=_transfer, args=(filename,)).start()
    return jsonify({'filename': filename}), 202
