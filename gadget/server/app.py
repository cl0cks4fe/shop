from flask import Flask
import os
from pathlib import Path
from config import Config
from routes import bp


def create_app():
    app = Flask(__name__, template_folder=Path(__file__).parent / 'templates')
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(16))
    Path(Config.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    if Config.DEV_MODE:
        Path(Config.TRANSFER_FOLDER).mkdir(parents=True, exist_ok=True)
    app.register_blueprint(bp)
    return app


if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=Config.PORT)
