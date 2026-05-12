import requests, pathlib
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QSettings, QTimer, QThread, Signal, QDateTime
from PySide6.QtGui import QShortcut, QKeySequence

EXTS = {".nc", ".gcode", ".tap", ".cnc", ".ngc", ".dxf", ".txt", ".step", ".stp", ".stl", ".svg", ".igs", ".iges", ".dwg"}


def flash_label(label, text, ms=3000):
    label.setText(text)
    QTimer.singleShot(ms, lambda: label.setText(""))


def reset_button(btn, text, ms=5000):
    QTimer.singleShot(ms, lambda: (btn.setEnabled(True), btn.setText(text), btn.setStyleSheet("")))


class PingWorker(QThread):
    finished = Signal(bool)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            ok = requests.get(f'http://{self.url}/api/ping', timeout=1).status_code == 200
        except Exception:
            ok = False
        self.finished.emit(ok)


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
            self.finished.emit(r.status_code == 202, "Success" if r.status_code == 202 else f"Error: {r.status_code}")
        except Exception:
            self.finished.emit(False, "Failed")


class SettingsTab(QWidget):
    path_changed = Signal(str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

        self.url = QLineEdit(settings.value("upload_url", "localhost:3000"))
        self.url.setFocusPolicy(Qt.ClickFocus)
        self.test_btn = QPushButton("Test Connection", clicked=self.test_upload_url)

        self.root_path = QLineEdit(settings.value("root_path", "~/"))
        self.root_path.setFocusPolicy(Qt.ClickFocus)

        self.save_status = QLabel("")

        form = QFormLayout()
        form.addRow("Gadget URL:", self._row(self.url, self.test_btn))
        form.addRow("Root Path:", self._row(self.root_path, QPushButton("Browse...", clicked=self.browse_path)))

        footer = QHBoxLayout()
        footer.addWidget(self.save_status)
        footer.addStretch()
        footer.addWidget(QPushButton("Discard", clicked=self.revert_settings))
        footer.addWidget(QPushButton("Apply", clicked=self.save_all))

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addStretch()
        layout.addLayout(footer)

    def _row(self, *widgets):
        row = QHBoxLayout()
        for w in widgets:
            row.addWidget(w)
        return row

    def browse_path(self):
        d = QFileDialog.getExistingDirectory(self, "Select Root Directory", self.root_path.text())
        if d:
            self.root_path.setText(d)

    def save_all(self):
        new_path = self.root_path.text()
        self.settings.setValue("upload_url", self.url.text())
        self.settings.setValue("root_path", new_path)
        self.settings.sync()
        self.path_changed.emit(new_path)
        flash_label(self.save_status, "Settings Applied")

    def revert_settings(self):
        self.url.setText(self.settings.value("upload_url", "localhost:3000"))
        self.root_path.setText(self.settings.value("root_path", "~/"))
        flash_label(self.save_status, "Changes Discarded", ms=2000)

    def test_upload_url(self):
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Connecting...")
        self.worker = PingWorker(self.url.text())
        self.worker.finished.connect(self.on_test_finished)
        self.worker.start()

    def on_test_finished(self, success):
        self.test_btn.setText("Online" if success else "Offline")
        self.test_btn.setStyleSheet(f"background-color: {'green' if success else 'red'}; color: white;")
        reset_button(self.test_btn, "Test Connection")


class LogsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.log_viewer = QPlainTextEdit(readOnly=True)
        self.log_viewer.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: monospace; font-size: 10pt;")
        QVBoxLayout(self).addWidget(self.log_viewer)

    def add_log(self, message):
        ts = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.log_viewer.appendPlainText(f"[{ts}] {message}")


class NotesTab(QTextEdit):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setPlainText(settings.value("notes", ""))
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

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 10, 20, 10)
        right_layout.addWidget(self.tabs)

        split = QSplitter(Qt.Horizontal)
        w = QWidget()
        w.setLayout(left)
        split.addWidget(w)
        split.addWidget(right)
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
        if pathlib.Path(self.model.filePath(parent)) >= self.ROOT:
            self.browser.setRootIndex(parent)
            self.update_nav()

    def update_nav(self):
        curr = pathlib.Path(self.model.filePath(self.browser.rootIndex()))
        self.up_btn.setEnabled(curr != self.ROOT)
        self.path_lbl.setText(f"{self.ROOT.name}/{curr.relative_to(self.ROOT) if curr != self.ROOT else ''}")

    def send_file(self):
        path = pathlib.Path(self.model.filePath(self.browser.currentIndex()))
        if not path.is_file():
            self.send_btn.setText("No file selected")
            reset_button(self.send_btn, "Send File")
            return

        self.send_btn.setEnabled(False)
        self.send_btn.setText("Sending...")
        self.worker = UploadWorker(self.settings.value("upload_url", ""), path)
        self.worker.finished.connect(self.on_upload_finished)
        self.worker.start()

    def on_upload_finished(self, success, message):
        filename = pathlib.Path(self.worker.file_path).name
        self.logs_tab.add_log(
            f"Upload succeeded: {filename}" if success else f"Upload failed: {filename} — {message}"
        )
        self.send_btn.setText(message)
        self.send_btn.setStyleSheet(f"background: {'green' if success else 'red'}; color: white;")
        reset_button(self.send_btn, "Send File")

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
