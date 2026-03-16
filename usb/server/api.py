import threading
import logging
import os
import time, shutil, subprocess
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

api_bp = Blueprint('api', __name__, url_prefix='/api')

class TransferState:
    def __init__(self):
        self._active_transfer = None
        self._lock = threading.Lock()

    def get_active_transfer(self):
        with self._lock:
            return self._active_transfer

    def set_active_transfer(self, value):
        with self._lock:
            self._active_transfer = value

transfer_state = TransferState()

@api_bp.route('/status')
def status():
    return jsonify({
        'device_name': current_app.config.get('DEVICE_NAME'),
        'active_transfer': transfer_state.get_active_transfer()
    })

@api_bp.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': 'No file provided'}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({'error': 'Invalid filename'}), 400

    active_transfer = transfer_state.get_active_transfer()
    if active_transfer:
        return jsonify({'error': f'"{active_transfer}" is transferring, please wait'}), 409
    else:
        transfer_state.set_active_transfer(filename)

    upload_path = os.path.join(current_app.config.get('UPLOAD_DIR'), filename)
    file.save(upload_path)

    try:
        if current_app.config.get('DEV_MODE'):
            time.sleep(5)
            shutil.copy2(upload_path, os.path.join(current_app.config.get('TRANSFER_DIR'), filename))
            os.unlink(upload_path)
        else:
            subprocess.run([current_app.config.get('TRANSFER_SCRIPT')], check=True, timeout=120)
    except Exception as e:
        logging.error(f'Transfer failed: {e}')
        return jsonify({'error': 'Transfer failed'}), 500
    finally:
        transfer_state.set_active_transfer(None)
    return jsonify({'filename': filename}), 202
