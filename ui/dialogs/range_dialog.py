from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox)
from PyQt5.QtCore import Qt
from matplotlib.patches import Rectangle
from ui.canvas_widget import MplCanvas

class RangeDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Set Ranges")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
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

        title = QLabel("Data range")
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


class RangeDialogAd(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Adapt Training Parameters")
        self.setFixedSize(700, 600)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        self.data = data.copy()
        self.canvas = MplCanvas(self)
        self.preview = MplCanvas(self)

        self.rect = None
        self.dragging = False
        self.start_drag = (0, 0)
        self.rect_origin = (0, 0)

        self.x_from = QLineEdit("0")
        self.y_from = QLineEdit("0")

        self.batch = QLineEdit("5")
        self.iterations = QLineEdit("1")
        self.epochs = QLineEdit("30")
        self.gensamples = QLineEdit("100")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Select the box to extract the noise")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E1E;")
        layout.addWidget(title)

        layout.addLayout(self._row("X:", self.x_from, "Y:", self.y_from))
        layout.addLayout(self._row("Batch:", self.batch, "Iterations:", self.iterations))
        layout.addLayout(self._row("Epochs:", self.epochs, "Samples:", self.gensamples))

        layout.addLayout(self._dual_canvas("Original Image", "Preview (128x128)"))

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

        self.canvas.mpl_connect("button_press_event", self.on_mouse_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("button_release_event", self.on_mouse_release)

        self.update_plot(0, 0)

    def _row(self, label1, field1, label2, field2):
        row = QHBoxLayout()
        row.addWidget(QLabel(label1))
        row.addWidget(field1)
        row.addWidget(QLabel(label2))
        row.addWidget(field2)
        return row

    def _dual_canvas(self, label1, label2):
        layout = QHBoxLayout()
        canvas_layout = QVBoxLayout()
        canvas_layout.addWidget(QLabel(label1))
        canvas_layout.addWidget(self.canvas)
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel(label2))
        preview_layout.addWidget(self.preview)
        layout.addLayout(canvas_layout)
        layout.addLayout(preview_layout)
        return layout

    def update_plot(self, x, y):
        x = max(0, min(int(x), self.data.shape[1] - 128))
        y = max(0, min(int(y), self.data.shape[0] - 128))

        self.x_from.setText(str(x))
        self.y_from.setText(str(y))

        self.canvas.ax.clear()
        self.canvas.ax.imshow(self.data.T, cmap="gray", origin="upper")

        self.rect = Rectangle((x, y), 128, 128, linewidth=2, edgecolor='cyan', facecolor='none')
        self.canvas.ax.add_patch(self.rect)
        self.canvas.draw()

        preview_data = self.data[y:y + 128, x:x + 128]
        self.preview.ax.clear()
        self.preview.ax.imshow(preview_data.T, cmap='gray', origin='upper')
        self.preview.draw()

    def on_mouse_press(self, event):
        if event.inaxes != self.canvas.ax:
            return
        contains = self.rect.contains_point((event.x, event.y))
        if contains:
            self.dragging = True
            self.start_drag = (event.xdata, event.ydata)
            self.rect_origin = self.rect.get_xy()

    def on_mouse_move(self, event):
        if not self.dragging or event.xdata is None or event.ydata is None:
            return

        dx = int(event.xdata - self.start_drag[0])
        dy = int(event.ydata - self.start_drag[1])
        new_x = int(self.rect_origin[0]) + dx
        new_y = int(self.rect_origin[1]) + dy
        new_x = max(0, min(new_x, self.data.shape[1] - 128))
        new_y = max(0, min(new_y, self.data.shape[0] - 128))

        self.update_plot(new_x, new_y)

    def on_mouse_release(self, event):
        self.dragging = False

    def get_ranges(self):
        x = int(self.x_from.text())
        y = int(self.y_from.text())
        return x, x + 128, y, y + 128

    def get_train_data(self):
        return (int(self.batch.text()), int(self.iterations.text()),
                int(self.epochs.text()), int(self.gensamples.text()))

class RangeDialog3D(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Set 3D Slice")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(460, 520)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        self.data = data.copy() if data is not None else None
        self.canvas = MplCanvas(self)
        self.mode = "inline"

        # Toggle Buttons
        self.inline_btn = QPushButton("Inline")
        self.crossline_btn = QPushButton("Crossline")
        self.inline_btn.setCheckable(True)
        self.crossline_btn.setCheckable(True)
        self.inline_btn.setChecked(True)

        for btn in [self.inline_btn, self.crossline_btn]:
            btn.setMinimumHeight(36)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    border: none;
                    padding: 6px 12px;
                    text-align: center;
                    color: #1E1E1E;
                    font-size: 13px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #F0F0F0;
                }
                QPushButton:checked {
                    background-color: #04BFAD;
                    color: white;
                }
            """)

        self.inline_btn.clicked.connect(self.set_inline_mode)
        self.crossline_btn.clicked.connect(self.set_crossline_mode)

        self.spin = QSpinBox()
        self.spin.setMinimum(0)
        self.spin.setMaximum(0)
        self.spin.setSingleStep(1)
        self.spin.setStyleSheet("""
            QSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                padding: 4px;
                font-size: 13px;
            }
        """)
        self.spin.valueChanged.connect(self.update_plot)

        # Layout principal
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Select Slice (Inline/Crossline)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1E1E1E;")
        layout.addWidget(title)

        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(self.inline_btn)
        toggle_layout.addWidget(self.crossline_btn)
        layout.addLayout(toggle_layout)
        layout.addLayout(self._row("Index:", self.spin))
        layout.addWidget(self.canvas)

        # Botones
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
        self.configure_spin_limits()
        self.update_plot()

    def _row(self, label, widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addWidget(widget)
        return row

    def configure_spin_limits(self):
        if self.data is not None and self.data.ndim == 3:
            d, h, w = self.data.shape
            self.spin.setMaximum(d - 1 if self.mode == "inline" else w - 1)

    def set_inline_mode(self):
        self.mode = "inline"
        self.inline_btn.setChecked(True)
        self.crossline_btn.setChecked(False)
        self.configure_spin_limits()
        self.update_plot()

    def set_crossline_mode(self):
        self.mode = "crossline"
        self.crossline_btn.setChecked(True)
        self.inline_btn.setChecked(False)
        self.configure_spin_limits()
        self.update_plot()

    def update_plot(self):
        if self.data is None or self.data.ndim != 3:
            return

        idx = self.spin.value()
        self.canvas.ax.clear()

        if self.mode == "inline":
            section = self.data[idx, :, :]
        else:
            section = self.data[:, :, idx]

        self.canvas.ax.imshow(section.T, cmap="gray", origin="upper", aspect="auto")
        self.canvas.draw()

    def get_slice(self):
        return {
            "mode": self.mode,
            "index": self.spin.value()
        }
