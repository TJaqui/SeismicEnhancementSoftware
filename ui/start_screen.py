from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from paths import resource_path

class StartScreen(QWidget):
    def __init__(self, on_open_clicked, parent=None):
        super(StartScreen, self).__init__(parent)
        self.setObjectName("startScreen")
        self.setStyleSheet("""
            #startScreen {
                background-color: #F9F9F9;
            }
            QLabel#titleLabel {
                font-size: 48px;
                font-weight: bold;
                color: #1E1E1E;
                font-family: 'Segoe UI';
            }
            QLabel#descLabel {
                font-size: 18px;
                color: #555;
                padding: 0 60px;
                font-family: 'Segoe UI';
            }
            QPushButton#openButton {
                background-color: #2979FF;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 14px 36px;
                border: none;
                border-radius: 14px;
            }
            QPushButton#openButton:hover {
                background-color: #1565C0;
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(40)
        layout.setContentsMargins(100, 100, 100, 100)

        # Logo aún más grande
        logo = QLabel()
        pixmap = QPixmap(resource_path("resources/icons/logo.png"))
        pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Título más grande
        title = QLabel("NED")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Descripción
        desc = QLabel("NED is a seismic processing software focused on enhancing 2D and 3D data using deep learning techniques.")
        desc.setObjectName("descLabel")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Botón abrir
        open_btn = QPushButton("OPEN")
        open_btn.setObjectName("openButton")
        open_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        open_btn.clicked.connect(on_open_clicked)
        layout.addWidget(open_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

