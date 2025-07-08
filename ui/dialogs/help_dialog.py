from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(420, 320)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(18)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Need help using the application?")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1E1E1E;")
        layout.addWidget(title)

        desc = QLabel("To find more information, usage examples, or troubleshooting tips, please visit our documentation wiki.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #4D4D4D;")
        layout.addWidget(desc)

        link_label = QLabel(
            '<a href="https://github.com/TJaqui/SeismicEnhancementSoftware/wiki">Visit our repository</a>'
        )
        link_label.setOpenExternalLinks(True)
        link_label.setWordWrap(True)
        link_label.setAlignment(Qt.AlignCenter)
        link_label.setStyleSheet("font-size: 14px; color: #2979FF;")
        layout.addWidget(link_label)

        footer = QLabel("© 2025 UIS")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Arial", 10))
        footer.setStyleSheet("color: #888888;")
        layout.addWidget(footer)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 8px 20px; border-radius: 8px; background-color: #2979FF; color: white; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)
