import logging
from flask import Flask, render_template, redirect, url_for
from api import api_bp, DEVICE_NAME

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(api_bp)

@app.route('/')
def index():
    return redirect(url_for('upload'))

@app.route('/upload')
def upload():
    return render_template('upload.html', device_name=DEVICE_NAME)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
