from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QCheckBox)
from PyQt5.QtCore import Qt
from matplotlib.widgets import RectangleSelector
from ui.canvas_widget import MplCanvas

class RangeDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Set Ranges")
        self.setFixedSize(420, 460)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        self.data = data.copy()
        self.canvas = MplCanvas(self)

        self.x_from = QLineEdit("0")
        self.x_to = QLineEdit(str(data.shape[1]) if data is not None else "500")
        self.y_from = QLineEdit("0")
        self.y_to = QLineEdit(str(data.shape[0]) if data is not None else "500")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Select data range")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1E1E1E;")
        layout.addWidget(title)

        layout.addLayout(self._row("X from:", self.x_from, "to", self.x_to))
        layout.addLayout(self._row("Y from:", self.y_from, "to", self.y_to))

        layout.addWidget(self.canvas)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Confirm")
        cancel_btn = QPushButton("Cancel")

        ok_btn.setStyleSheet("padding: 8px 20px; border-radius: 8px; background-color: #2979FF; color: white; font-weight: bold;")
        cancel_btn.setStyleSheet("padding: 8px 20px; border-radius: 8px; background-color: #FFFFFF; color: #333; border: 1px solid #CCC;")

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        for box in [self.x_from, self.x_to, self.y_from, self.y_to]:
            box.textChanged.connect(self.update_plot)

        self.setLayout(layout)
        self.update_plot()

    def _row(self, label1, field1, label2, field2):
        row = QHBoxLayout()
        row.addWidget(QLabel(label1))
        row.addWidget(field1)
        row.addWidget(QLabel(label2))
        row.addWidget(field2)
        return row

    def get_ranges(self):
        return (int(self.x_from.text()), int(self.x_to.text()),
                int(self.y_from.text()), int(self.y_to.text()))

    def update_plot(self):
        try:
            x_start, x_end, y_start, y_end = self.get_ranges()
            if self.data is not None:
                cropped = self.data[y_start:y_end, x_start:x_end]
                self.canvas.ax.clear()
                self.canvas.ax.imshow(cropped.T, cmap="gray", origin="upper", aspect="equal")
                self.canvas.draw()
        except:
            pass


class RangeDialogAd(RangeDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent, data)
        self.setWindowTitle("Adapt Training Parameters")
        self.setFixedSize(460, 540)

        self.batch = QLineEdit("5")
        self.iterations = QLineEdit("1")
        self.epochs = QLineEdit("30")
        self.gensamples = QLineEdit("100")

        self.layout().insertLayout(3, self._row("Batch:", self.batch, "Iterations:", self.iterations))
        self.layout().insertLayout(4, self._row("Epochs:", self.epochs, "Samples:", self.gensamples))

        if self.data is not None:
            self.selector = RectangleSelector(
                self.canvas.ax,
                self.on_select,
                useblit=True,
                button=[1],
                minspanx=5,
                minspany=5,
                spancoords='pixels',
                interactive=True
            )
            self.canvas.draw()

    def get_train_data(self):
        return (int(self.batch.text()), int(self.iterations.text()),
                int(self.epochs.text()), int(self.gensamples.text()))

    def on_select(self, eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        x_start, x_end = sorted((x1, x2))
        y_start, y_end = sorted((y1, y2))
        self.x_from.setText(str(x_start))
        self.x_to.setText(str(x_end))
        self.y_from.setText(str(y_start))
        self.y_to.setText(str(y_end))
        self.update_plot()


class RangeDialogEn3D(QDialog):
    def __init__(self, parent=None, data=None, ilines=None, xlines=None):
        super().__init__(parent)
        self.setWindowTitle("Select 3D Section")
        self.setFixedSize(460, 540)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        self.data = data.copy() if data is not None else None
        self.canvas = MplCanvas(self)

        self.whole_cube_checkbox = QCheckBox("Whole 3D Cube")
        self.section_checkbox = QCheckBox("Section of Cube")
        self.whole_cube_checkbox.setChecked(True)
        self.section_checkbox.setChecked(False)
        self.whole_cube_checkbox.stateChanged.connect(self.toggle_mode)
        self.section_checkbox.stateChanged.connect(self.toggle_mode)

        self.x_from = QLineEdit("0")
        self.x_to = QLineEdit(str(data.shape[1]) if data is not None else "500")
        self.y_from = QLineEdit("0")
        self.y_to = QLineEdit(str(data.shape[0]) if data is not None else "500")
        self.iline_from = QLineEdit(str(ilines[0]) if ilines is not None else "500")
        self.iline_to = QLineEdit(str(ilines[-1]) if ilines is not None else "500")
        self.crossline_from = QLineEdit(str(xlines[0]) if xlines is not None else "500")
        self.crossline_to = QLineEdit(str(xlines[-1]) if xlines is not None else "500")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self.whole_cube_checkbox)
        layout.addWidget(self.section_checkbox)
        layout.addLayout(self._row("X from:", self.x_from, "to", self.x_to))
        layout.addLayout(self._row("Y from:", self.y_from, "to", self.y_to))
        layout.addLayout(self._row("Iline from:", self.iline_from, "to", self.iline_to))
        layout.addLayout(self._row("Crossline from:", self.crossline_from, "to", self.crossline_to))
        layout.addWidget(self.canvas)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Confirm")
        cancel_btn = QPushButton("Cancel")
        ok_btn.setStyleSheet("padding: 8px 20px; border-radius: 8px; background-color: #2979FF; color: white; font-weight: bold;")
        cancel_btn.setStyleSheet("padding: 8px 20px; border-radius: 8px; background-color: #FFFFFF; color: #333; border: 1px solid #CCC;")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.toggle_mode()
        self.update_plot()

    def _row(self, label1, field1, label2, field2):
        row = QHBoxLayout()
        row.addWidget(QLabel(label1))
        row.addWidget(field1)
        row.addWidget(QLabel(label2))
        row.addWidget(field2)
        return row

    def toggle_mode(self):
        is_whole = self.whole_cube_checkbox.isChecked()
        self.section_checkbox.setChecked(not is_whole)

        for widget in [self.x_from, self.x_to, self.y_from, self.y_to,
                       self.iline_from, self.iline_to, self.crossline_from, self.crossline_to]:
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
                self.canvas.ax.imshow(self.data.T, cmap="gray", origin="upper", aspect="equal")
            else:
                x0, x1 = ranges["x"]
                y0, y1 = ranges["y"]
                cropped = self.data[y0:y1, x0:x1]
                self.canvas.ax.imshow(cropped.T, cmap="gray", origin="upper", aspect="equal")

            self.canvas.draw()
        except:
            pass
