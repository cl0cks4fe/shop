from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import logging

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

@app.route('/ping', methods=['GET'])
def ping():
    gadget_id = request.headers.get('id')
    logger.debug(f'registering device: {gadget_id} ({request.host})')
    if gadget_id not in gadgets:
        gadgets[gadget_id] = Gadget(gadget_id, request.remote_addr)
    gadgets[gadget_id].last_seen = datetime.now()
    return "ok", 200

@app.route('/logs', methods=['POST'])
def logs():
    print(request.json)
    return jsonify({"message": "ingested"}), 201

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', gadgets=gadgets)

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=3000)
