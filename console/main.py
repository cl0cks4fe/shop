import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter, QListView, QTabWidget, QLabel
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Q:
            self.close()
        else:
            super().keyPressEvent(event)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Machine Shop Console")

        splitter = QSplitter(Qt.Horizontal)

        # Left: File browser placeholder
        file_browser = QListView()
        splitter.addWidget(file_browser)

        # Right: Tabbed tools placeholder
        tabs = QTabWidget()
        tabs.addTab(QLabel("Calculator tool coming soon..."), "Calculator")
        tabs.addTab(QLabel("Other tool coming soon..."), "Other Tool")
        splitter.addWidget(tabs)

        # splitter.setSizes([250, 650])

        central_widget = QWidget()
        layout = QHBoxLayout(central_widget)
        layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())
