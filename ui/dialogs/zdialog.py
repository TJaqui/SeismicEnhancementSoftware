from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QRadioButton, QMessageBox, QButtonGroup, QSpinBox)
from PyQt5.QtCore import Qt
from matplotlib.patches import Rectangle
from ui.canvas_widget import MplCanvas


class ZDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("View Z-slice")
        self.setFixedSize(700, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        self.data = data
        self.canvas = MplCanvas(self)

        # SpinBox to move through dim2
        self.slice_selector = QSpinBox()
        self.slice_selector.setRange(0, data.shape[1] - 1)  # dim2
        self.slice_selector.setValue(data.shape[1] // 2)
        self.slice_selector.valueChanged.connect(self.update_plot)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Z-Slice Viewer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1E1E1E;")
        layout.addWidget(title)

        spin_layout = QHBoxLayout()
        spin_layout.addWidget(QLabel("Z-slice index:"))
        spin_layout.addWidget(self.slice_selector)
        layout.addLayout(spin_layout)

        layout.addWidget(self.canvas)

        
        self.setLayout(layout)
        self.update_plot()

    def update_plot(self):
        index = self.slice_selector.value()

        try:
          
            self.canvas.ax.clear()

            # XY slice at dim2 = index
            
            self.canvas.ax.imshow(self.data[:, index, :], cmap="gray", origin="upper", aspect="equal")
            self.canvas.ax.set_title(f'{index}')

            self.canvas.draw()
        except Exception as e:
            print("Plotting error:", e)