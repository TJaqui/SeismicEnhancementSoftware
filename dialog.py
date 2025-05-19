import os
import sys
import segyio
import utils
import time
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets
from PyQt5.uic import loadUi
from finetuning import parallelTrain
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy 
from PyQt5.QtWidgets import QButtonGroup
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QVBoxLayout, QGraphicsDropShadowEffect, QCheckBox, QFrame, QProgressBar, QMessageBox, QLineEdit, QPushButton, QHBoxLayout, QLabel, QDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)  
        super().__init__(fig)
        self.zoom_factor = 1.2  # Factor for zooming in/out
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def wheelEvent(self, event):
        """Handles mouse scroll for zooming."""
        zoom_in = event.angleDelta().y() > 0  # Detect scroll direction
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        x_range = (xlim[1] - xlim[0]) / (self.zoom_factor if zoom_in else 1/self.zoom_factor)
        y_range = (ylim[1] - ylim[0]) / (self.zoom_factor if zoom_in else 1/self.zoom_factor)

        self.ax.set_xlim([x_center - x_range / 2, x_center + x_range / 2])
        self.ax.set_ylim([y_center - y_range / 2, y_center + y_range / 2])
        self.draw()


class RangeDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Set Ranges")
        self.setFixedSize(400, 400)

        self.data = data.copy()
        self.canvas = MplCanvas(self)

        self.x_from = QLineEdit("0")
        self.x_to = QLineEdit(str(data.shape[1]) if data is not None else "500")
        self.y_from = QLineEdit("0")
        self.y_to = QLineEdit(str(data.shape[0]) if data is not None else "500")

        layout = QVBoxLayout()

        # X Range
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("x from"))
        x_layout.addWidget(self.x_from)
        x_layout.addWidget(QLabel("-"))
        x_layout.addWidget(self.x_to)
        layout.addLayout(x_layout)

        # Y Range
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("y from"))
        y_layout.addWidget(self.y_from)
        y_layout.addWidget(QLabel("-"))
        y_layout.addWidget(self.y_to)
        layout.addLayout(y_layout)

        # Canvas for plot
        layout.addWidget(self.canvas)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("ok")
        cancel_btn = QPushButton("cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # Update preview when values change
        for box in [self.x_from, self.x_to, self.y_from, self.y_to]:
            box.textChanged.connect(self.update_plot)

        self.setLayout(layout)
        self.update_plot()  # Initial preview

    def get_ranges(self):
        return (int(self.x_from.text()), int(self.x_to.text()),
                int(self.y_from.text()), int(self.y_to.text()))
    

    def update_plot(self):
        try:
            x_start, x_end, y_start, y_end = self.get_ranges()
            if self.data is not None:
                cropped = self.data[y_start:y_end, x_start:x_end]
                self.canvas.ax.clear()
                self.canvas.ax.imshow(cropped, cmap="gray")
                self.canvas.draw()
        except Exception as e:
            # Ignore invalid input temporarily
            pass
from matplotlib.widgets import RectangleSelector

class RangeDialogAd(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Set Ranges")
        self.setFixedSize(400, 400)

        self.data = data
        self.canvas = MplCanvas(self)

        self.x_from = QLineEdit("0")
        self.x_to = QLineEdit(str(data.shape[1]) if data is not None else "500")
        self.y_from = QLineEdit("0")
        self.y_to = QLineEdit(str(data.shape[0]) if data is not None else "500")
        self.batch = QLineEdit("5")
        self.iterations = QLineEdit("1")
        self.epochs = QLineEdit("30")
        self.gensamples = QLineEdit("100")

        layout = QVBoxLayout()

        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("x from"))
        x_layout.addWidget(self.x_from)
        x_layout.addWidget(QLabel("-"))
        x_layout.addWidget(self.x_to)
        layout.addLayout(x_layout)

        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("y from"))
        y_layout.addWidget(self.y_from)
        y_layout.addWidget(QLabel("-"))
        y_layout.addWidget(self.y_to)
        layout.addLayout(y_layout)

        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Batch"))
        z_layout.addWidget(self.batch)
        z_layout.addWidget(QLabel("Iterations"))
        z_layout.addWidget(self.iterations)
        layout.addLayout(z_layout)

        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Epochs"))
        a_layout.addWidget(self.epochs)
        a_layout.addWidget(QLabel("Samples"))
        a_layout.addWidget(self.gensamples)
        layout.addLayout(a_layout)

        layout.addWidget(self.canvas)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("ok")
        cancel_btn = QPushButton("cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        if self.data is not None:
            self.canvas.ax.imshow(self.data, cmap="gray")
            self.selector = RectangleSelector(
                self.canvas.ax,
                self.on_select,
                useblit=True,
                button=[1],  # Left click
                minspanx=5,
                minspany=5,
                spancoords='pixels',
                interactive=True
            )
            self.canvas.draw()

    def on_select(self, eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)

        # Ordenar coordenadas
        x_start, x_end = sorted((x1, x2))
        y_start, y_end = sorted((y1, y2))

        self.x_from.setText(str(x_start))
        self.x_to.setText(str(x_end))
        self.y_from.setText(str(y_start))
        self.y_to.setText(str(y_end))

        self.update_plot()

    def get_ranges(self):
        return (int(self.x_from.text()), int(self.x_to.text()),
                int(self.y_from.text()), int(self.y_to.text()))
    def get_train_data(self):
        return (int(self.batch.text()), int(self.iterations.text()),
                int(self.epochs.text()), int(self.gensamples.text()))

    def update_plot(self):
        try:
            x_start, x_end, y_start, y_end = self.get_ranges()
            if self.data is not None:
                cropped = self.data[y_start:y_end, x_start:x_end]
                self.canvas.ax.clear()
                self.canvas.ax.imshow(cropped, cmap="gray")
                self.canvas.draw()
        except Exception:
            pass

class DialogDim(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select data dimensions")
        self.setFixedSize(200, 200)

    
        self.d3 = QCheckBox("3D")
        self.d2 = QCheckBox("2D")

        # Conectar para comportamiento exclusivo
        self.d3.stateChanged.connect(self.on_d3_checked)
        self.d2.stateChanged.connect(self.on_d2_checked)

        layout = QVBoxLayout()
        x_layout = QHBoxLayout()
        x_layout.addWidget(self.d3)
        x_layout.addWidget(self.d2)
        layout.addLayout(x_layout)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("ok")
        cancel_btn = QPushButton("cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def on_d3_checked(self, state):
        if state:
            self.d2.setChecked(False)

    def on_d2_checked(self, state):
        if state:
            self.d3.setChecked(False)

    def get_Checked(self):
        if self.d3.isChecked():
            return True, False
        if self.d2.isChecked():
            return False, True
