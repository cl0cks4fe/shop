import os
from pathlib import Path

def _is_dev_mode():
    return os.environ.get('DEV', '').lower() in ('1', 'true', 'yes', 'on')

def _get_device_name():
    if _is_dev_mode():
        return 'dev'
    else:
        try:
            return Path('/etc/gadget-device-name').read_text().strip()
        except FileNotFoundError:
            return 'unknown'

class Config(object):
    DEV_MODE = _is_dev_mode()
    DEVICE_NAME = _get_device_name()
    TRANSFER_SCRIPT = str(Path(__file__).parent / 'scripts' / 'transfer.sh')
    UPLOAD_DIR = str(Path(__file__).parent / Path('upload'))
    TRANSFER_DIR = str(Path(__file__).parent / Path('transferred')) if DEV_MODE else None
