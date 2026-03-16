import sys
import requests
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QTreeView, QVBoxLayout,
    QSplitter, QTabWidget, QLabel, QPushButton, QFileSystemModel, QTextEdit,
    QHeaderView, QLineEdit, QFormLayout, QGroupBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("console", "Settings")
        
        layout = QVBoxLayout(self)
        self.group_box = QGroupBox("USB Gadget")
        box_layout = QFormLayout(self.group_box)

        self.url_input = QLineEdit(self.settings.value("upload_url", "localhost:3000"))
        box_layout.addRow("Gadget URL:", self.url_input)

        btns = QWidget()
        btn_layout = QHBoxLayout(btns)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        
        self.save_btn = QPushButton("Save", clicked=self.save_settings)
        self.test_btn = QPushButton("Test", clicked=self.test_connection)
        self.status = QLabel()
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.test_btn)
        btn_layout.addStretch() 
        btn_layout.addWidget(self.status) 
        
        box_layout.addRow(btns)
        layout.addWidget(self.group_box)
        layout.addStretch()

    def save_settings(self):
        self.settings.setValue("upload_url", self.url_input.text())
        self.status.setText("<font color='green'><b>✓ Saved</b></font>")
        QTimer.singleShot(5000, lambda: self.status.setText(""))

    def test_connection(self):
        try:
            requests.get(f'http://{self.url_input.text()}/ping', timeout=3)
            self.status.setText("<font color='green'>Connected</font>")
        except:
            self.status.setText("<font color='red'>Offline</font>")

class MainWindow(QMainWindow):
    ROOT_PATH = Path("/home/cl0ck/projects/example").resolve()

    def __init__(self):
        super().__init__()
        self.settings = QSettings("console", "Settings")
        self.setWindowTitle("Shop Console")
        
        self.model = QFileSystemModel()
        self.model.setRootPath(str(self.ROOT_PATH))
        
        self.file_browser = QTreeView()
        self.path_label = QLabel(f"{self.ROOT_PATH.name}")
        self.viewer_text = QTextEdit(readOnly=True)
        self.up_btn = QPushButton("⟵", fixedWidth=48, clicked=self.navigate_up)
        self.up_btn.setStyleSheet("font-weight: bold")
        self.up_btn.setEnabled(False)
        self.viewer_title = QLabel()
        
        self.setup_ui()
        self.setup_shortcuts()

    def setup_ui(self):
        self.file_browser.setModel(self.model)
        self.file_browser.setRootIndex(self.model.index(str(self.ROOT_PATH)))
        self.file_browser.clicked.connect(self.on_file_selected)
        self.file_browser.doubleClicked.connect(self.on_directory_double_clicked)
        self.file_browser.hideColumn(1)
        self.file_browser.hideColumn(2)
        self.file_browser.setExpandsOnDoubleClick(False)
        self.file_browser.setRootIsDecorated(False)
        self.file_browser.setItemsExpandable(False) 
        self.file_browser.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_browser.setStyleSheet("font-size: 14pt;")

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.up_btn)
        nav_layout.addWidget(self.path_label, 1)

        self.send_btn = QPushButton("", minimumHeight=80)
        self.reset_send_button()
        self.send_btn.clicked.connect(self.send_file)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addLayout(nav_layout)
        left_layout.addWidget(self.file_browser)
        left_layout.addWidget(self.send_btn)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("font-size: 14pt;")
        
        viewer_page = QWidget()
        v_layout = QVBoxLayout(viewer_page)
        v_layout.addWidget(self.viewer_title)
        v_layout.addWidget(self.viewer_text)
        self.tabs.addTab(viewer_page, "Viewer")

        self.settings_tab = SettingsTab()
        self.tabs.addTab(self.settings_tab, "Settings")

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.tabs)
        splitter.setSizes([500, 500])

        container = QWidget()
        main_layout = QHBoxLayout(container)
        main_layout.addWidget(splitter)
        self.setCentralWidget(container)

    def send_file(self):
        index = self.file_browser.currentIndex()
        if not index.isValid() or self.model.isDir(index):
            return

        target_url = self.settings.value("upload_url", "")
        file_path = self.model.filePath(index)
        file_name = Path(file_path).name

        self.send_btn.setText(f"Sending {file_name}...")
        self.send_btn.setEnabled(False) 
        QApplication.processEvents()

        try:
            with open(file_path, 'rb') as f:
                r = requests.post(f'http://{target_url}/api/upload', files={'file': f}, timeout=10)
            
            if r.status_code == 202:
                self.send_btn.setText("✓ Successful")
                self.send_btn.setStyleSheet("background-color: green; color: white; font-weight: bold; font-size: 18px;")
            else:
                self.send_btn.setText(f"Error: {r.status_code}")
                self.send_btn.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 18px;")
                
        except Exception as e:
            self.send_btn.setText("Connection Failed")
            self.send_btn.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 18px;")
        
        QTimer.singleShot(2000, self.reset_send_button)

    def update_path_label(self):
        cur_root = Path(self.model.filePath(self.file_browser.rootIndex()))
        if cur_root == self.ROOT_PATH:
            self.path_label.setText(self.ROOT_PATH.name)
        else:
            relative_path = cur_root.relative_to(self.ROOT_PATH)
            self.path_label.setText(f'{self.ROOT_PATH.name}/{relative_path}')

    def reset_send_button(self):
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send File")
        self.send_btn.setStyleSheet("font-size: 18px; font-weight: bold;")

    def on_file_selected(self, index):
        path = Path(self.model.filePath(index))
        if path.is_file():
            content = path.read_text(encoding='utf-8', errors='replace')
            self.viewer_title.setText(f"<b>{path.name}</b>")
            self.viewer_text.setPlainText(content)
            self.tabs.setCurrentIndex(0)

    def on_directory_double_clicked(self, index):
        if self.model.isDir(index):
            self.file_browser.setRootIndex(index)
            self.update_path_label()
            self.up_btn.setEnabled(True)

    def navigate_up(self):
        curr = self.file_browser.rootIndex()
        parent = curr.parent()
        parent_path = Path(self.model.filePath(parent)).resolve()
        if parent.isValid():
            self.file_browser.setRootIndex(parent)
        if parent_path == self.ROOT_PATH:
            self.up_btn.setEnabled(False)
        self.update_path_label()

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())