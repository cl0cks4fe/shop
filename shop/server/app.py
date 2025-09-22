from flask import Flask
import logging

from config import Config
from extensions import db
from blueprints.devices import devices_bp


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M')

    db.init_app(app)
    app.register_blueprint(devices_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=3000)
