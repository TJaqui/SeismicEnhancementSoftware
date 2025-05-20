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
from matplotlib.widgets import RectangleSelector
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

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



class RangeDialogEn3D(QDialog):
    def __init__(self, parent=None, data=None, ilines=None, xlines=None ):
        super().__init__(parent)
        self.setWindowTitle("Set Ranges")
        self.setFixedSize(450, 500)

        self.data = data.copy() if data is not None else None
        self.canvas = MplCanvas(self)

        self.whole_cube_checkbox = QCheckBox("Whole 3D Cube")
        self.section_checkbox = QCheckBox("Section of Cube")

        self.whole_cube_checkbox.setChecked(True)
        self.section_checkbox.setChecked(False)

        self.whole_cube_checkbox.stateChanged.connect(self.toggle_mode)
        self.section_checkbox.stateChanged.connect(self.toggle_mode)
        # Create range input fields
        self.x_from = QLineEdit("0")
        self.x_to = QLineEdit(str(data.shape[1]) if data is not None else "500")
        self.y_from = QLineEdit("0")
        self.y_to = QLineEdit(str(data.shape[0]) if data is not None else "500")
        self.iline_from = QLineEdit(str(ilines[0]) if ilines is not None else "500")
        self.iline_to = QLineEdit(str(ilines[-1]) if ilines is not None else "500")
        self.crossline_from = QLineEdit(str(xlines[0]) if xlines is not None else "500")
        self.crossline_to = QLineEdit(str(xlines[-1]) if xlines is not None else "500")

        layout = QVBoxLayout()

        # Mode selection
        layout.addWidget(self.whole_cube_checkbox)
        layout.addWidget(self.section_checkbox)
       
        # Section inputs
        section_layout = QVBoxLayout()

        # X Range
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("x from"))
        x_layout.addWidget(self.x_from)
        x_layout.addWidget(QLabel("-"))
        x_layout.addWidget(self.x_to)
        section_layout.addLayout(x_layout)

        # Y Range
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("y from"))
        y_layout.addWidget(self.y_from)
        y_layout.addWidget(QLabel("-"))
        y_layout.addWidget(self.y_to)
        section_layout.addLayout(y_layout)

        # Iline
        iline_layout = QHBoxLayout()
        iline_layout.addWidget(QLabel("iline from"))
        iline_layout.addWidget(self.iline_from)
        iline_layout.addWidget(QLabel("-"))
        iline_layout.addWidget(self.iline_to)
        section_layout.addLayout(iline_layout)

        # Crossline
        cl_layout = QHBoxLayout()
        cl_layout.addWidget(QLabel("crossline from"))
        cl_layout.addWidget(self.crossline_from)
        cl_layout.addWidget(QLabel("-"))
        cl_layout.addWidget(self.crossline_to)
        section_layout.addLayout(cl_layout)

        layout.addLayout(section_layout)

        # Canvas preview
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
       
        # Connect updates
        for box in [self.x_from, self.x_to, self.y_from, self.y_to,
                    self.iline_from, self.iline_to, self.crossline_from, self.crossline_to]:
            box.textChanged.connect(self.update_plot)

        self.setLayout(layout)
        self.toggle_mode()
        self.update_plot()

    def toggle_mode(self):
        is_whole = self.whole_cube_checkbox.isChecked()
        self.section_checkbox.setChecked(not is_whole)

        for widget in [self.x_from, self.x_to, self.y_from, self.y_to,
                       self.iline_from,self.iline_to , self.crossline_from, self.crossline_to]:
            widget.setEnabled(not is_whole)

    def get_ranges(self):
        if self.whole_cube_checkbox.isChecked():
            return "whole", None
        else:
            return "section", {
                "x": (int(self.x_from.text()), int(self.x_to.text())),
                "y": (int(self.y_from.text()), int(self.y_to.text())),
                "iline": (int(self.iline_from.text()), int(self.iline_to.text())),
                "crossline": (int(self.crossline_from.text()), int(self.crossline_to.text()))
            }

    def update_plot(self):
        try:
            if self.data is None:
                return

            mode, ranges = self.get_ranges()
            self.canvas.ax.clear()

            if mode == "whole":
                # Just show a middle slice in one view for preview
                #middle = self.data.shape[0] // 2
                self.canvas.ax.imshow(self.data, cmap="gray")
            else:
                x0, x1 = ranges["x"]
                y0, y1 = ranges["y"]
                # For simplicity show a 2D slice at iline
                
                cropped = self.data[y0:y1, x0:x1]
                self.canvas.ax.imshow(cropped, cmap="gray")

            self.canvas.draw()
        except Exception as e:
            pass  # Invalid input is ignored for now



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


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        # Project description
        title = QLabel("NED")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("This project was developed by the following contributors,\n"
                      "In aims to provide useful tools for data visualization and seismic processing.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Contributors/icons
        contributors_layout = QHBoxLayout()
        icon_paths = ["icons/Logos_collaborators.png"]  # Update these to actual file paths

        for icon_path in icon_paths:
            try:
                pixmap = QPixmap(icon_path).scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label = QLabel()
                icon_label.setPixmap(pixmap)
                icon_label.setAlignment(Qt.AlignCenter)
                contributors_layout.addWidget(icon_label)
            except Exception as e:
                print(f"Failed to load icon {icon_path}: {e}")

        layout.addLayout(contributors_layout)

        # Footer
        footer = QLabel("© 2025 HDSP")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Arial", 10))
        layout.addWidget(footer)

        self.setLayout(layout)

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        # Project description
        desc = QLabel("To find information about the software,\n"
                      "please, consult the wiki.")

        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        link_label = QLabel(
            '<a href="https://github.com/TJaqui/SeismicEnhancementSoftware/wiki">Visit our repository</a>'
        )
        link_label.setOpenExternalLinks(True)
        link_label.setWordWrap(True)
        link_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(link_label)
        
        # Footer
        footer = QLabel("© 2025 HDSP")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Arial", 10))
        layout.addWidget(footer)

        self.setLayout(layout)