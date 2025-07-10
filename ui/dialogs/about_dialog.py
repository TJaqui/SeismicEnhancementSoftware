from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,QSizePolicy
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(580, 500)
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

        desc = QLabel("This work was funded by the Vicerrectoría de Investigacion y Extensi´on from Universidad Industrial de Santander under Project 3925.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #4D4D4D;")
        layout.addWidget(desc)

        than = QLabel("This work was funded by the Vicerrectoría de Investigacion y Extensión from Universidad Industrial de Santander under Project 3925.")
        than.setWordWrap(True)
        than.setAlignment(Qt.AlignCenter)
        than.setStyleSheet("font-size: 13px; color: #4D4D4D;")
        layout.addWidget(than)

        contributors_layout = QVBoxLayout()
        contributors_layout.setAlignment(Qt.AlignCenter)

        # === Top row: 4 logos ===
        top_row_layout = QHBoxLayout()
        top_row_layout.setAlignment(Qt.AlignCenter)

        top_logos = [
            "resources/icons/GrupoGIRG.png",
            "resources/icons/GrupoGIGBA.png",
            "resources/icons/hdsp.png",
        ]
        maximun_size=[(50,70),(70,50),(70,50)]
        for path,maximun_size in zip(top_logos,maximun_size):
            print(path, maximun_size)
            try:
                pixmap = QPixmap(path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label = QLabel()
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignCenter)
                label.setFixedSize(100, 100)  # Make the label exactly the same size
                top_row_layout.addWidget(label)
            except Exception as e:
                print(f"Failed to load {path}: {e}")

        contributors_layout.addLayout(top_row_layout)

        # === Bottom row: 1 centered logo ===
        bottom_logo_path = "resources/icons/uis.png"
        try:
            pixmap = QPixmap(bottom_logo_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(100, 100)
            contributors_layout.addWidget(label, alignment=Qt.AlignHCenter)
        except Exception as e:
            print(f"Failed to load {bottom_logo_path}: {e}")

        # === Add to main layout ===
        layout.addLayout(contributors_layout)



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