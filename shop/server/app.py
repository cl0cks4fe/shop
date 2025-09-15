from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import logging
import threading

app = Flask(__name__)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M')

class Gadget:
    def __init__(self, id, url):
        self.id = id
        self.url = f'http://{url}:3000'
        self.last_seen = None
    def connected(self):
        return self.last_seen and (datetime.now() - self.last_seen) <= timedelta(minutes=1)

gadgets = {}
gadgets_lock = threading.Lock()

@app.route('/ping', methods=['GET'])
def ping():
    gadget_id = request.headers.get('id')
    if not gadget_id:
        logger.warning('Missing gadget id in headers')
        return "Missing gadget id", 400
    logger.debug(f'Registering device: {gadget_id} ({request.host})')
    with gadgets_lock:
        if gadget_id not in gadgets:
            gadgets[gadget_id] = Gadget(gadget_id, request.remote_addr)
        gadgets[gadget_id].last_seen = datetime.now()
    return "ok", 200

@app.route('/logs', methods=['POST'])
def logs():
    data = request.get_json(force=True, silent=True)
    if not data or 'log' not in data:
        logger.warning('Invalid log data received')
        return jsonify({"error": "Invalid log data"}), 400
    logger.info(f"Log from device: {data['log']}")
    return jsonify({"message": "ingested"}), 201

@app.route('/', methods=['GET'])
def index():
    with gadgets_lock:
        return render_template('index.html', gadgets=gadgets)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
