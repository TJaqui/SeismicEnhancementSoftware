from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt5.QtCore import Qt

class ProgressDialog(QDialog):
    def __init__(self, title="Processing", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setStyleSheet("background-color: #F9FAFB; border-radius: 12px;")

        layout = QVBoxLayout()
        layout.setSpacing(12)

        self.label = QLabel("Processing... Please wait.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 14px; color: #4D4D4D;")
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #E6F7F5;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
            }
            QProgressBar::chunk {
                background-color: #04BFAD;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def update_progress(self, value: int, message: str = ""):
        self.progress_bar.setValue(value)
        if message:
            self.label.setText(message)
        QApplication.processEvents()


