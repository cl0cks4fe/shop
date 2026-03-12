import os, shutil, subprocess, threading, time, logging
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

_active = None
_lock = threading.Lock()

_script = Path(__file__).parent / 'scripts' / 'transfer.sh'


def get_active():
    with _lock:
        return _active


def save_file(file):
    if not file or not file.filename:
        raise ValueError("No file provided")
    filename = os.path.basename(file.filename)
    file.save(os.path.join(Config.UPLOAD_FOLDER, filename))
    return filename


def start_transfer(file):
    filename = save_file(file)

    global _active
    with _lock:
        if _active is not None:
            return False
        _active = filename

    def run():
        global _active
        try:
            if Config.DEV_MODE:
                time.sleep(2)
                src = Path(Config.UPLOAD_FOLDER) / filename
                shutil.copy2(src, Path(Config.TRANSFER_FOLDER) / filename)
                src.unlink()
            else:
                subprocess.run([str(_script)], check=True, timeout=120)
            logger.info(f"Transfer successful: {filename}")
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
        finally:
            with _lock:
                _active = None

    threading.Thread(target=run).start()
    return True
