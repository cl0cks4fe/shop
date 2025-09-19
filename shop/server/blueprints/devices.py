from flask import Blueprint, request, render_template
from datetime import datetime
from extensions import db
from models import Device

devices_bp = Blueprint('devices', __name__, url_prefix='/devices')

@devices_bp.route('/ping', methods=['GET'])
def ping():
    gadget_id = request.headers.get('id')
    gadget_port = request.headers.get('port', '80')
    if not gadget_id:
        return "Missing gadget id", 400
    url = f'{request.remote_addr}:{gadget_port}'
    now = datetime.now().isoformat()
    device = db.session.get(Device, gadget_id)
    if device is None:
        device = Device(id=gadget_id, url=url, last_seen=now)
        db.session.add(device)
    else:
        device.url = url
        device.last_seen = now
    db.session.commit()
    return "ok", 200


@devices_bp.route('/', methods=['GET'])
def index():
    devices = Device.query.all()
    return render_template('devices.html', devices=devices)
