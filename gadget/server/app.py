from flask import Flask, request, render_template, redirect, url_for
import os
import subprocess
import time
import threading
import logging
import requests

from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def allowed_file(filename):
    # Placeholder: extend to check extensions
    return True


def secure_filename(filename):
    return os.path.basename(filename)

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

    app.config.from_object(Config)

    # Ensure upload folder exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    def run_transfer_script(filename):
        """Run transfer script in background thread"""
        try:
            subprocess.run([os.path.join(os.getcwd(), 'scripts/transfer.sh')], check=True)
            logger.info(f"Transfer script completed for file: {filename}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Transfer script failed for file {filename}: {e}")

    @app.route('/ping', methods=['GET'])
    def ping():
        return 'ok', 200

    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        if request.method == 'POST':
            if 'file' not in request.files:
                return 'No file selected', 400
            file = request.files['file']
            filename = secure_filename(file.filename)
            if filename == '' or not allowed_file(filename):
                return 'Invalid file type', 400
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            try:
                file.save(filepath)
            except Exception as e:
                logger.error(f"File save failed: {e}")
                return 'File save failed', 500
            
            # Start transfer script in background thread
            transfer_thread = threading.Thread(target=run_transfer_script, args=(filename,))
            transfer_thread.daemon = True
            transfer_thread.start()
            
            logger.info(f"File uploaded: {filename} (transfer script running in background)")
            return redirect(url_for('upload', success=True))
        
        success = request.args.get('success')
        return render_template('upload.html', success=success, device_name=Config.DEVICE_NAME)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html', device_name=Config.DEVICE_NAME)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT)
