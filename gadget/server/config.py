import os


def get_device_name():
    try:
        with open('/etc/gadget-device-name', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return 'unknown'


class Config:
    DEV_MODE = os.environ.get('DEV_MODE', '').lower() in ('1', 'true', 'yes', 'on')
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
    if DEV_MODE: TRANSFER_FOLDER = os.path.join(os.getcwd(), 'transferred')
    PORT = int(os.environ.get('GADGET_PORT', 3000))
    DEVICE_NAME = 'dev' if DEV_MODE else get_device_name()
