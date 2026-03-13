import logging
from flask import Flask, render_template, redirect, url_for
from api import api_bp
from config import Config
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(api_bp)


@app.route('/')
def index():
    return redirect(url_for('upload'))


@app.route('/upload')
def upload():
    return render_template('upload.html', device_name=app.config.get('DEVICE_NAME'))


if __name__ == '__main__':
    os.makedirs(app.config.get('UPLOAD_DIR'), exist_ok=True)
    if app.config.get('DEV_MODE'): os.makedirs(app.config.get('TRANSFER_DIR'), exist_ok=True)
    app.run(host='0.0.0.0', port=3000)
