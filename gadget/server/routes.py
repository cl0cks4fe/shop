"""
Flask Blueprint for gadget routes.
"""
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, current_app
import logging

from config import Config

logger = logging.getLogger(__name__)

# Create the blueprint
bp = Blueprint('main', __name__)


def get_services():
    """Get services from current app context."""
    return current_app.transfer_service, current_app.file_handler


@bp.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint."""
    transfer_service, _ = get_services()
    return jsonify({
        'status': 'ok',
        'device_name': Config.DEVICE_NAME,
        'transfer_active': transfer_service.is_transfer_active(),
        'active_transfer': transfer_service.get_active_transfer(),
        'dev_mode': Config.DEV_MODE
    }), 200


@bp.route('/status', methods=['GET'])
def status():
    """Get current system status."""
    transfer_service, _ = get_services()
    status_info = {
        'device_name': Config.DEVICE_NAME,
        'transfer_active': transfer_service.is_transfer_active(),
        'active_transfer': transfer_service.get_active_transfer(),
        'upload_folder': Config.UPLOAD_FOLDER,
        'dev_mode': Config.DEV_MODE
    }

    if Config.DEV_MODE:
        status_info['transfer_folder'] = Config.TRANSFER_FOLDER

    return jsonify(status_info)


@bp.route('/upload', methods=['GET', 'POST'])
def upload():
    """Handle file upload."""
    transfer_service, file_handler = get_services()

    if request.method == 'POST':
        try:
            # Validate file presence
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('main.upload'))

            file = request.files['file']

            # Save file using FileHandler
            filename, filepath = file_handler.save_uploaded_file(file, Config.UPLOAD_FOLDER)

            # Try to start transfer
            if transfer_service.start_transfer(filename):
                flash(f'File "{filename}" uploaded and transfer started!', 'success')
            else:
                active_file = transfer_service.get_active_transfer()
                flash(f'Transfer busy with "{active_file}". Please wait.', 'warning')

            return redirect(url_for('main.upload'))

        except ValueError as e:
            flash(str(e), 'error')
            logger.warning(f"Upload validation error: {e}")
            return redirect(url_for('main.upload'))
        except Exception as e:
            flash('An error occurred during upload', 'error')
            logger.error(f"Upload error: {e}")
            return redirect(url_for('main.upload'))

    # GET request - show upload form
    return render_template(
        'upload.html',
        device_name=Config.DEVICE_NAME,
        transfer_active=transfer_service.is_transfer_active(),
        active_transfer=transfer_service.get_active_transfer()
    )


@bp.route('/', methods=['GET'])
def index():
    """Home page."""
    transfer_service, _ = get_services()
    return render_template(
        'index.html',
        device_name=Config.DEVICE_NAME,
        transfer_active=transfer_service.is_transfer_active(),
        active_transfer=transfer_service.get_active_transfer()
    )


@bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500
