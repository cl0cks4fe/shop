from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from config import Config
from file_transfer import get_active, start_transfer

bp = Blueprint('main', __name__)


@bp.route('/status')
def status():
    info = {'device_name': Config.DEVICE_NAME}
    active_transfer = get_active()
    if active_transfer:
        info['active_transfer'] = active_transfer
    return jsonify(info)


@bp.route('/', methods=['GET'])
def upload_get():
    return render_template('upload.html', device_name=Config.DEVICE_NAME, active_transfer=get_active())


@bp.route('/', methods=['POST'])
def upload_post():
    active_transfer = get_active()
    if active_transfer:
        flash(f'"{active_transfer}" is transferring, please wait', 'warning')
    else:
        try:
            start_transfer(request.files.get('file'))
        except Exception as e:
            flash(f'"transfer failed, {e}', 'error')

    return redirect(url_for('main.upload_get'))
