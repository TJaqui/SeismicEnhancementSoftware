from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QPushButton, QButtonGroup, QFileDialog
from PyQt5.QtCore import Qt

class SelectModeDialog(QDialog):
    def __init__(self, parent=None):
        super(SelectModeDialog, self).__init__(parent)
        self.setWindowTitle("Select data dimensions")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(320, 180)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        self.selected_mode = "2D"
        self.selected_file = ""

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        title = QLabel("Select data dimensions")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1E1E1E;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.radio_2d = QRadioButton("2D")
        self.radio_3d = QRadioButton("3D")
        self.radio_2d.setChecked(True)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio_2d, alignment=Qt.AlignCenter)
        radio_layout.addWidget(self.radio_3d, alignment=Qt.AlignCenter)
        layout.addLayout(radio_layout)

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.radio_2d)
        self.button_group.addButton(self.radio_3d)

        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("padding: 8px 20px; border-radius: 8px; background-color: #FFFFFF; color: #333; border: 1px solid #CCC;")
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("Confirm")
        ok_btn.setStyleSheet("padding: 8px 20px; border-radius: 8px; background-color: #2979FF; color: white; font-weight: bold;")
        ok_btn.clicked.connect(self.on_confirm)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def on_confirm(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open seismic file', '', 'SEGY files (*.sgy *.segy);;All files (*)')
        if file_path:
            self.selected_file = file_path
            self.selected_mode = "2D" if self.radio_2d.isChecked() else "3D"
            self.accept()

    def get_mode(self):
        return self.selected_mode

    def get_file_path(self):
        return self.selected_file
