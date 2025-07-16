from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from ui.canvas_widget import MplCanvas
from utils import save2dData, save3dData
from pathlib import Path

class SaveDataDialog(QDialog):
    def __init__(self, data, dataEnhanced, data_name, mode, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Data")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(600, 560)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        self.data = data
        self.dataEnhanced = dataEnhanced
        self.data_name = data_name
        self.mode = mode

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Select location...")
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Enter filename...")

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(80)
        browse_btn.setStyleSheet("background-color: #2979FF; color: white; border-radius: 6px; padding: 6px 12px;")
        browse_btn.clicked.connect(self.browse_location)

        location_layout = QHBoxLayout()
        location_layout.addWidget(self.location_input)
        location_layout.addWidget(browse_btn)

        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: 500; color: #1E1E1E;")

        self.canvas = MplCanvas(self)
        self.update_plot()

        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.setStyleSheet("padding: 8px 20px; border-radius: 8px; background-color: #04BFAD; color: white; font-weight: bold;")
        cancel_btn.setStyleSheet("padding: 8px 20px; border-radius: 8px; background-color: #E0E0E0; color: #1E1E1E;")
        save_btn.clicked.connect(self.save_data)
        cancel_btn.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        layout.addLayout(location_layout)
        layout.addWidget(self.filename_input)
        layout.addWidget(preview_label)
        layout.addWidget(self.canvas)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def browse_location(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            self.location_input.setText(path)

    def update_plot(self):
        self.canvas.ax.clear()
        if self. mode =="2D":
            if self.dataEnhanced is not None:
                self.canvas.ax.imshow(self.dataEnhanced, cmap="gray", origin="upper", aspect="equal")
            else:
                self.canvas.ax.imshow(self.data, cmap="gray", origin="upper", aspect="equal")
        elif self.mode == "3D":
            if self.dataEnhanced is not None:
                self.canvas.ax.imshow(self.dataEnhanced[100], cmap="gray", origin="upper", aspect="equal")
            else:
                self.canvas.ax.imshow(self.data[100], cmap="gray", origin="upper", aspect="equal")
        self.canvas.draw()

    def save_data(self):
        folder = self.location_input.text().strip()
        filename = self.filename_input.text().strip()

        if not folder or not filename:
            QMessageBox.warning(self, "Missing Info", "Please select a location and filename.")
            return

        folder_path = Path(folder)
        if not folder_path.exists() or not folder_path.is_dir():
            QMessageBox.critical(self, "Error", "Invalid folder path.")
            return

        dst_path = folder_path / (filename + ".sgy")
        data_to_save = self.dataEnhanced.T if self.dataEnhanced is not None else self.data.T

        try:
            dmin, dmax = data_to_save.min(), data_to_save.max()
            if self.mode == "2D":
                save2dData(data_to_save, self.data_name, dst_path, dmin, dmax)
            elif self.mode == "3D":
                save3dData(data_to_save, self.data_name, dst_path, dmin, dmax)

            QMessageBox.information(self, "Success", f"Data saved successfully to:\n{dst_path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data:\n{e}")