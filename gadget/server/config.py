import os
import threading


def get_device_name():
    try:
        with open('/etc/gadget-device-name', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return 'unknown'


class Config:
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
    SHOP_URL = os.environ.get('SHOP_URL', 'http://192.168.0.118:3000')
    PORT = int(os.environ.get('GADGET_PORT', 3000))
    DEVICE_NAME = get_device_name()
    CONNECTED_FLAG = threading.Event()
