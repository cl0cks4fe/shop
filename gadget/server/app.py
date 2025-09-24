from flask import Flask
import os
import logging
from pathlib import Path

from config import Config
from file_transfer import FileHandler, TransferService
from routes import bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, template_folder=Path(__file__).parent / 'templates')
    app.config.from_object(Config)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

    # Initialize services
    transfer_service = TransferService(Config)
    file_handler = FileHandler()

    # Ensure upload folder exists
    Path(Config.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

    # In dev mode, also ensure transfer folder exists
    if Config.DEV_MODE and Config.TRANSFER_FOLDER:
        Path(Config.TRANSFER_FOLDER).mkdir(parents=True, exist_ok=True)
        logger.info(f"Running in DEV MODE - transfers will go to: {Config.TRANSFER_FOLDER}")

    # Store services on app object for blueprint access
    app.transfer_service = transfer_service
    app.file_handler = file_handler

    # Register blueprint
    app.register_blueprint(bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT)
