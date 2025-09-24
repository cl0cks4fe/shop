import os
import threading


def get_device_name():
    try:
        with open('/etc/gadget-device-name', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return 'dev-machine' if os.environ.get('DEV_MODE') else 'unknown'


class Config:
    # Development mode - set DEV_MODE=1 to run locally without hardware scripts
    DEV_MODE = os.environ.get('DEV_MODE', '').lower() in ('1', 'true', 'yes', 'on')

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')

    # In dev mode, also create a transfer destination folder
    TRANSFER_FOLDER = os.path.join(os.getcwd(), 'transferred') if DEV_MODE else None

    SHOP_URL = os.environ.get('SHOP_URL', 'http://192.168.0.118:3000')
    PORT = int(os.environ.get('GADGET_PORT', 3000))
    DEVICE_NAME = get_device_name()
    CONNECTED_FLAG = threading.Event()
