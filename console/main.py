import sys
import subprocess
import requests
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QTreeView, QVBoxLayout,
    QSplitter, QTabWidget, QLabel, QPushButton, QFileSystemModel, QTextEdit,
    QHeaderView, 
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

class MainWindow(QMainWindow):
    ROOT_PATH = Path("/home/cl0ck/projects/example").resolve()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shop Console")
        
        self.model = QFileSystemModel()
        self.model.setRootPath(str(self.ROOT_PATH))
        
        self.file_browser = QTreeView()
        self.path_label = QLabel(f"{self.ROOT_PATH.name}")
        self.viewer_text = QTextEdit(readOnly=True, placeholderText="")
        self.viewer_title = QLabel()
        
        self.setup_ui()
        self.setup_shortcuts()

    def setup_ui(self):
        self.file_browser.setModel(self.model)
        self.file_browser.setRootIndex(self.model.index(str(self.ROOT_PATH)))
        self.file_browser.clicked.connect(self.on_file_selected)
        self.file_browser.doubleClicked.connect(self.on_directory_double_clicked)

        # columns are: name, size, type, date
        self.file_browser.hideColumn(1) # size
        self.file_browser.hideColumn(2) # type
        self.file_browser.header().setStretchLastSection(True)
        self.file_browser.header().setSectionResizeMode(0, QHeaderView.Stretch)
        
        self.file_browser.setExpandsOnDoubleClick(False)
        self.file_browser.setRootIsDecorated(False)
        self.file_browser.setItemsExpandable(False)
        self.file_browser.setStyleSheet("font-size: 14pt;")

        # Navigation Bar
        nav_layout = QHBoxLayout()
        up_btn = QPushButton("↑", fixedWidth=48, clicked=self.navigate_up)
        up_btn.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.path_label.setStyleSheet("padding-left: 8px; font-size: 18px;")

        nav_layout.addWidget(up_btn)
        nav_layout.addWidget(self.path_label, 1)

        # Action Buttons
        self.send_btn = QPushButton("Send", minimumHeight=80)
        self.send_btn.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.send_btn.clicked.connect(self.send_file)
        self.send_btn.setEnabled(True)

        # Left Sidebar Assembly
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addLayout(nav_layout)
        left_layout.addWidget(self.file_browser)
        left_layout.addWidget(self.send_btn)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Right Tabs Assembly
        self.tabs = QTabWidget()

        self.calc_btn = QPushButton("🖩 Calculator", minimumHeight=30)
        self.calc_btn.clicked.connect(self.open_calculator)
        self.tabs.setCornerWidget(self.calc_btn, Qt.TopRightCorner)
        self.tabs.setStyleSheet("font-size: 14pt;")

        viewer_page = QWidget()
        v_layout = QVBoxLayout(viewer_page)
        v_layout.addWidget(self.viewer_title)
        v_layout.addWidget(self.viewer_text)
        
        self.tabs.addTab(viewer_page, "Viewer")
        self.tabs.addTab(QLabel("Tool A Coming Soon", alignment=Qt.AlignCenter), "Tool A")

        # Main Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.tabs)
        splitter.setSizes([10000, 20000])
        container = QWidget()
        main_layout = QHBoxLayout(container)
        
        main_layout.setContentsMargins(12, 12, 12, 12) 
        
        main_layout.addWidget(splitter)
        self.setCentralWidget(container)

    def open_calculator(self):
        try:
            subprocess.Popen(["gnome-calculator", "--mode=advanced"]) 
        except FileNotFoundError:
            print("Calculator app not found.")

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)

    def on_file_selected(self, index):
        path = Path(self.model.filePath(index))
        if path.is_file():
            self.show_file_contents(path)
        else:
            self.viewer_title.setText("")
            self.viewer_text.clear()

    def show_file_contents(self, path: Path):
        try:
            content = path.read_text(encoding='utf-8', errors='replace')
            self.viewer_title.setText(f"<b>{path.name}</b>")
            self.viewer_text.setPlainText(content)
            self.tabs.setCurrentIndex(0)
        except Exception as e:
            self.viewer_text.setPlainText(f"Could not read file: {e}")

    def on_directory_double_clicked(self, index):
        if self.model.isDir(index):
            new_path = Path(self.model.filePath(index))
            self.update_root(new_path)
            self.viewer_title.setText("")
            self.viewer_text.clear()

    def navigate_up(self):
        current_root = Path(self.model.filePath(self.file_browser.rootIndex()))
        parent = current_root.parent
        self.viewer_title.setText("")
        self.viewer_text.clear()
        if current_root != self.ROOT_PATH and parent.is_relative_to(self.ROOT_PATH):
            self.update_root(parent)

    def update_root(self, path: Path):
        self.file_browser.setRootIndex(self.model.index(str(path)))
        rel = path.relative_to(self.ROOT_PATH)
        self.path_label.setText(f"{self.ROOT_PATH.name}/{rel}" if str(rel) != "." else f"{self.ROOT_PATH.name}")

    def send_file(self):
        index = self.file_browser.currentIndex()
        if not index.isValid() or self.model.isDir(index):
            return

        file_path = self.model.filePath(index)
        try:
            with open(file_path, 'rb') as f:
                r = requests.post(f'http://localhost:3000/upload', files={'file': f}, timeout=10)
            
            if r.status_code == 200:
                print(f"Success: {Path(file_path).name} uploaded.")
            else:
                print(f"Failed: HTTP {r.status_code}")
        except Exception as e:
            print(f"Network Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())