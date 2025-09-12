from flask import Flask, request, jsonify, render_template
import time
import requests
import threading
import logging

app = Flask(__name__)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M')

class Gadget:
    def __init__(self, id, url, port):
        self.id = id
        self.url = url
        self.port = port

gadgets = []

@app.route('/register', methods=['POST'])
def register():
    gadget_id = request.json.get('id')
    port = request.json.get('port', '8080')
    logger.debug(f'registering device: {gadget_id} ({request.remote_addr})')
    if not gadget_id:
        return jsonify({"error": "no id provided"}, 400)
    if gadget_id not in [gadget.id for gadget in gadgets]:
        gadgets.append(Gadget(gadget_id, request.remote_addr, port))
    return jsonify({"message": "Gadget registered successfully", "gadget": gadget_id}), 201

@app.route('/logs', methods=['POST'])
def logs():
    print(request.json)
    return jsonify({"message": "ingested"}), 201

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', gadgets=gadgets)

def ping_gadgets():
    global gadgets
    while True:
        alive = []
        for gadget in gadgets:
            logger.debug(f'pinging: {gadget.id} ({gadget.url})')
            try:
                response = requests.get(f'http://{gadget.url}:{gadget.port}/ping')
            except:
                pass
            if response.status_code == 200:
                logger.debug(f'success: {gadget.id} ({gadget.url})')
                alive.append(gadget)
            else:
                logger.debug(f'failure: {gadget.id} ({gadget.url})')
        gadgets = alive
        time.sleep(5)

if __name__ == '__main__':
    ping_thread = threading.Thread(target=ping_gadgets, daemon=True)
    ping_thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)
