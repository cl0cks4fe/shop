import requests, pathlib
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QSettings, QTimer, QThread, Signal, QDateTime
from PySide6.QtGui import QShortcut, QKeySequence

EXTS = {".nc", ".gcode", ".tap", ".cnc", ".ngc", ".dxf", ".txt", ".step", ".stp", ".stl", ".svg", ".igs", ".iges", ".dwg"}

class PingWorker(QThread):
    finished = Signal(bool)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            r = requests.get(f'http://{self.url}/ping', timeout=1)
            self.finished.emit(r.status_code == 200)
        except Exception:
            self.finished.emit(False)

class UploadWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, url, file_path):
        super().__init__()
        self.url = url
        self.file_path = file_path

    def run(self):
        try:
            with open(self.file_path, 'rb') as f:
                r = requests.post(f'http://{self.url}/api/upload', files={'file': f})
            
            if r.status_code == 202:
                self.finished.emit(True, "Success")
            else:
                self.finished.emit(False, f"Error: {r.status_code}")
        except Exception:
            self.finished.emit(False, "Failed")

class SettingsTab(QWidget):
    path_changed = Signal(str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # upload url

        self.url = QLineEdit(self.settings.value("upload_url", "localhost:3000"))
        self.url.setFocusPolicy(Qt.ClickFocus)
        
        url_row = QHBoxLayout()
        url_row.addWidget(self.url)
        
        self.test_btn = QPushButton("Test Connection", clicked=self.test_upload_url)
        url_row.addWidget(self.test_btn)

        self.form_layout.addRow("Gadget URL:", url_row)

        # root path

        self.root_path = QLineEdit(self.settings.value("root_path", "~/"))
        self.root_path.setFocusPolicy(Qt.ClickFocus)

        path_row = QHBoxLayout()
        path_row.addWidget(self.root_path)
        path_row.addWidget(QPushButton("Browse...", clicked=self.browse_path))

        self.form_layout.addRow("Root Path:", path_row)

        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addStretch()

        # footer

        self.footer = QHBoxLayout()
        self.save_status = QLabel("")

        self.cancel_btn = QPushButton("Discard", clicked=self.revert_settings)
        self.save_btn = QPushButton("Apply", clicked=self.save_all)

        self.footer.addWidget(self.save_status)
        self.footer.addStretch()
        self.footer.addWidget(self.cancel_btn)
        self.footer.addWidget(self.save_btn)
        
        self.main_layout.addLayout(self.footer)

    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Root Directory", self.root_path.text())
        if directory:
            self.root_path.setText(directory)

    def save_all(self):
        new_path = self.root_path.text()
        self.settings.setValue("upload_url", self.url.text())
        self.settings.setValue("root_path", new_path)
        self.settings.sync()
        
        self.path_changed.emit(new_path)
        
        self.save_status.setText("Settings Applied")
        QTimer.singleShot(3000, lambda: self.save_status.setText(""))

    def revert_settings(self):
        self.url.setText(self.settings.value("upload_url", "localhost:3000"))
        self.root_path.setText(self.settings.value("root_path", "~/"))
        self.save_status.setText("Changes Discarded")
        QTimer.singleShot(2000, lambda: self.save_status.setText(""))

    def test_upload_url(self):
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Connecting...")
        
        self.worker = PingWorker(self.url.text())
        self.worker.finished.connect(self.on_test_finished)
        self.worker.start()

    def on_test_finished(self, success):
        if success:
            self.test_btn.setText("Online")
            self.test_btn.setStyleSheet("background-color: green; color: white;")
        else:
            self.test_btn.setText("Offline")
            self.test_btn.setStyleSheet("background-color: red; color: white;")
            
        QTimer.singleShot(5000, self.reset_test_button)

    def reset_test_button(self):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("Test Connection")
        self.test_btn.setStyleSheet("")

class LogsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.log_viewer = QPlainTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: monospace; font-size: 10pt;")
        layout.addWidget(self.log_viewer)

    def add_log(self, message):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.log_viewer.appendPlainText(f"[{timestamp}] {message}")

class NotesTab(QTextEdit):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        
        saved_notes = self.settings.value("notes", "")
        self.setPlainText(saved_notes)
        
        self.textChanged.connect(self.save_notes)

    def save_notes(self):
        self.settings.setValue("notes", self.toPlainText())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("console", "Settings")
        self.ROOT = pathlib.Path(self.settings.value("root_path", "~/")).expanduser().resolve()
        self.model = QFileSystemModel()
        self.model.setRootPath(str(self.ROOT))

        self.browser = QTreeView()
        self.viewer = QTextEdit(readOnly=True)
        self.path_lbl = QLabel(self.ROOT.name)
        self.send_btn = QPushButton("Send File", clicked=self.send_file, minimumHeight=80)
        self.up_btn = QPushButton(icon=self.style().standardIcon(QStyle.SP_ArrowBack), enabled=False, clicked=self.go_up)

        self.setup_ui()
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)

    def setup_ui(self):
        self.browser.setModel(self.model)
        self.browser.setRootIndex(self.model.index(str(self.ROOT)))
        self.browser.clicked.connect(self.preview)
        self.browser.doubleClicked.connect(self.go_down)
        self.browser.setExpandsOnDoubleClick(False)
        self.browser.setRootIsDecorated(False)
        self.browser.hideColumn(1)
        self.browser.hideColumn(2)
        self.browser.header().setSectionResizeMode(0, QHeaderView.Stretch)

        nav = QHBoxLayout()
        nav.addWidget(self.up_btn)
        nav.addWidget(self.path_lbl, 1)

        left = QVBoxLayout()
        left.addLayout(nav)
        left.addWidget(self.browser)
        left.addWidget(self.send_btn)

        self.settings_tab = SettingsTab(self.settings)
        self.settings_tab.path_changed.connect(self.update_root_directory)

        self.logs_tab = LogsTab()

        self.tabs = QTabWidget()

        self.tabs.addTab(self.viewer, "File Viewer")
        self.tabs.addTab(NotesTab(self.settings), "Notes")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.logs_tab, "Logs")

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel) 
        right_layout.setContentsMargins(0, 10, 20, 10) 
        right_layout.addWidget(self.tabs)

        split = QSplitter(Qt.Horizontal)
        w1 = QWidget()
        w1.setLayout(left)
        split.addWidget(w1)
        split.addWidget(right_panel)
        self.setCentralWidget(split)
        self.setStyleSheet("font-size: 14pt;")

    def preview(self, idx):
        p = pathlib.Path(self.model.filePath(idx))
        if p.is_file() and p.suffix in EXTS:
            self.viewer.setPlainText(p.read_text(errors='replace'))
            self.tabs.setCurrentIndex(0)

    def go_down(self, idx):
        if self.model.isDir(idx):
            self.browser.setRootIndex(idx)
            self.update_nav()

    def go_up(self):
       parent = self.browser.rootIndex().parent()
       parent_path = pathlib.Path(self.model.filePath(parent))
       if parent_path >= self.ROOT:
           self.browser.setRootIndex(parent)
           self.update_nav()

    def update_nav(self):
        curr = pathlib.Path(self.model.filePath(self.browser.rootIndex()))
        self.up_btn.setEnabled(curr != self.ROOT)
        self.path_lbl.setText(f"{self.ROOT.name}/{curr.relative_to(self.ROOT) if curr != self.ROOT else ''}")

    def send_file(self):
        idx = self.browser.currentIndex()
        path = pathlib.Path(self.model.filePath(idx))
        if not (path.is_file() and path.suffix in EXTS):
            self.send_btn.setText("No file selected")
            QTimer.singleShot(5000, self.reset_send_button)
            return
        
        url = self.settings.value("upload_url", "")
        
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Sending...")

        self.worker = UploadWorker(url, path)
        self.worker.finished.connect(self.on_upload_finished)
        self.worker.start()

    def on_upload_finished(self, success, message):
        filename = pathlib.Path(self.worker.file_path).name
        if success:
            self.logs_tab.add_log(f"Upload succeeded: {filename}")
        else:
            self.logs_tab.add_log(f"Upload failed: {filename} — {message}")

        self.send_btn.setText(message)
        self.send_btn.setStyleSheet(f"background: {'green' if success else 'red'}; color: white;")
        
        QTimer.singleShot(5000, self.reset_send_button)

    def reset_send_button(self):
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send File")
        self.send_btn.setStyleSheet("")

    def update_root_directory(self, path_str):
        self.ROOT = pathlib.Path(path_str).expanduser().resolve()
        
        self.model.setRootPath(str(self.ROOT))
        self.browser.setRootIndex(self.model.index(str(self.ROOT)))

        self.update_nav()


if __name__ == "__main__":
    app = QApplication([])
    win = MainWindow()
    win.showFullScreen()
    app.exec()
