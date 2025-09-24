"""
Service classes for file handling and transfer operations.
"""
import os
import subprocess
import threading
import logging
from pathlib import Path
from werkzeug.utils import secure_filename as werkzeug_secure_filename

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file operations and validation."""

    @staticmethod
    def is_allowed_file(filename):
        """Check if file extension is allowed."""
        if not filename:
            return False
        return True

    @staticmethod
    def secure_filename(filename):
        if not filename:
            return None
        secured = werkzeug_secure_filename(filename)
        return secured if secured else os.path.basename(filename)

    @staticmethod
    def save_uploaded_file(file, upload_folder):
        if not file or not file.filename:
            raise ValueError("No file provided")

        filename = FileHandler.secure_filename(file.filename)
        if not filename:
            raise ValueError("Invalid filename")

        if not FileHandler.is_allowed_file(filename):
            raise ValueError("File type not allowed")

        filepath = Path(upload_folder) / filename

        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            file.save(str(filepath))
            logger.info(f"File saved successfully: {filename}")
            return filename, str(filepath)
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            raise


class TransferService:
    """Handles file transfer operations."""

    def __init__(self, config):
        self.config = config
        self.transfer_script = Path(__file__).parent / 'scripts' / 'transfer.sh'
        self._active_transfer = None
        self._lock = threading.Lock()

    def is_transfer_active(self):
        with self._lock:
            return self._active_transfer is not None

    def get_active_transfer(self):
        with self._lock:
            return self._active_transfer

    def _dev_transfer(self, filename):
        """Development mode transfer - just copy files locally."""
        import shutil
        import time

        upload_folder = Path(self.config.UPLOAD_FOLDER)
        transfer_folder = Path(self.config.TRANSFER_FOLDER)

        # Ensure transfer folder exists
        transfer_folder.mkdir(parents=True, exist_ok=True)

        source_file = upload_folder / filename
        dest_file = transfer_folder / filename

        # Simulate some transfer time
        time.sleep(2)

        if source_file.exists():
            shutil.copy2(source_file, dest_file)
            source_file.unlink()
            logger.info(f"DEV MODE: Transferred {filename} to {dest_file}")
        else:
            raise FileNotFoundError(f"Source file not found: {source_file}")

    def _hardware_transfer(self, filename):
        """Production mode transfer - run the hardware script."""
        subprocess.run([str(self.transfer_script)], check=True, timeout=120)

    def start_transfer(self, filename):
        """Start transfer if none is active. Returns True if started, False if busy."""
        with self._lock:
            if self._active_transfer is not None:
                return False
            self._active_transfer = filename

        def run():
            try:
                logger.info(f"Starting transfer: {filename} (DEV_MODE: {self.config.DEV_MODE})")

                if self.config.DEV_MODE:
                    self._dev_transfer(filename)
                else:
                    self._hardware_transfer(filename)

                logger.info(f"Transfer completed: {filename}")
            except Exception as e:
                logger.error(f"Transfer failed for {filename}: {e}")
            finally:
                with self._lock:
                    self._active_transfer = None

        threading.Thread(target=run, name=f"transfer-{filename}").start()
        return True
