from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setFixedSize(420, 360)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(18)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("NED")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1E1E1E;")
        layout.addWidget(title)

        desc = QLabel("This project was developed to provide useful tools for data visualization and seismic enhancement.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #4D4D4D;")
        layout.addWidget(desc)

        contributors_layout = QHBoxLayout()
        contributors_layout.setAlignment(Qt.AlignCenter)

        icon_path = "resources/icons/Logos_collaborators.png"
        try:
            pixmap = QPixmap(icon_path).scaled(240, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label = QLabel()
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            contributors_layout.addWidget(icon_label)
        except Exception as e:
            print(f"Failed to load icon {icon_path}: {e}")

        layout.addLayout(contributors_layout)

        footer = QLabel("© 2025 HDSP")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Arial", 10))
        footer.setStyleSheet("color: #888888;")
        layout.addWidget(footer)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 8px 20px; border-radius: 8px; background-color: #2979FF; color: white; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)