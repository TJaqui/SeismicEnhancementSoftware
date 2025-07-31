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

class RangeDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Set Ranges")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(500, 500)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        self.data = data.copy()
        self.original_data = data.copy()
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

        # Botón "Pick in the canvas"
        pick_btn = QPushButton("Pick in the canvas")
        pick_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 500;
                color: white;
                background-color: #04BFAD;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #02A494;
            }
        """)
        pick_btn.setCursor(Qt.PointingHandCursor)
        pick_btn.clicked.connect(self.open_pick_dialog)

        pick_layout = QHBoxLayout()
        pick_layout.addStretch()
        pick_layout.addWidget(pick_btn)
        pick_layout.addStretch()
        layout.addLayout(pick_layout)

        layout.addSpacing(12)

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
            if self.original_data is not None:
                # Recortar desde la imagen original, no la actual
                cropped = self.original_data[y_start:y_end, x_start:x_end]
                self.data = cropped.copy()  # actualizar la imagen de trabajo (sin tocar el original)
                self.canvas.ax.clear()
                self.canvas.ax.imshow(cropped, cmap="gray", origin="upper", aspect="equal")
                self.canvas.draw()
        except:
            pass

    def open_pick_dialog(self):
        height, width = self.original_data.shape
        extent = (0, width, height, 0)  # izquierda, derecha, arriba, abajo
        dialog = PickInCanvasDialog(self, data=self.original_data, extent=extent)
        if dialog.exec_() == QDialog.Accepted:
            x1, x2, y1, y2 = dialog.get_selected_ranges()
            self.x_from.setText(str(x1))
            self.x_to.setText(str(x2))
            self.y_from.setText(str(y1))
            self.y_to.setText(str(y2))

class PickInCanvasDialog(QDialog):
    def __init__(self, parent=None, data=None, extent=None):
        super().__init__(parent)
        self.setWindowTitle("Pick in the canvas")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(700, 560)
        self.setStyleSheet("background-color: #FFFFFF;")

        self.data = data
        self.extent = extent
        self.start_pos = None
        self.end_pos = None
        self.rect_patch = None
        self.selected_ranges = None
        self.is_selecting = False

        self.canvas = MplCanvas(self)
        self.canvas.setFixedSize(660, 440)
        self.ax = self.canvas.ax

        self.ax.imshow(self.data, cmap="gray", origin="upper", aspect='auto', extent=self.extent)
        self.ax.set_xlabel("X", fontsize=12, color="#1E1E1E")
        self.ax.set_ylabel("Y", fontsize=12, color="#1E1E1E")
        self.ax.tick_params(axis='both', colors='#4D4D4D', labelsize=10)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)

        self.ax.set_title("Please select an area of at least 128x128 pixels", fontsize=12)

        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.canvas.mpl_connect("button_release_event", self.on_release)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(self.canvas)

        self.ok_btn = QPushButton("Confirm")
        self.ok_btn.setFixedWidth(160)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #2979FF;
                color: white;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        self.ok_btn.clicked.connect(self.confirm_selection)
        layout.addWidget(self.ok_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def on_press(self, event):
        if event.inaxes != self.ax or self.is_selecting:
            return
        self.start_pos = (event.xdata, event.ydata)
        self.end_pos = None
        self.is_selecting = True
        if self.rect_patch:
            self.rect_patch.remove()
        self.rect_patch = Rectangle(self.start_pos, 0, 0, linewidth=2, edgecolor="#04BFAD", facecolor='none')
        self.ax.add_patch(self.rect_patch)

    def on_motion(self, event):
        if not self.is_selecting or not self.start_pos or event.inaxes != self.ax:
            return
        self.end_pos = (event.xdata, event.ydata)
        x0, y0 = self.start_pos
        dx = self.end_pos[0] - x0
        dy = self.end_pos[1] - y0
        self.rect_patch.set_width(dx)
        self.rect_patch.set_height(dy)
        self.canvas.draw_idle()

    def on_release(self, event):
        if not self.is_selecting or not self.start_pos or not self.end_pos:
            return
        self.is_selecting = False
        x0, y0 = self.start_pos
        x1, y1 = self.end_pos
        x_from, x_to = sorted([int(x0), int(x1)])
        y_from, y_to = sorted([int(y0), int(y1)])
        self.selected_ranges = (x_from, x_to, y_from, y_to)

    def confirm_selection(self):
        if not self.selected_ranges:
            QMessageBox.warning(self, "Area not selected", "Please select an area on the image.")
            return

        x_from, x_to, y_from, y_to = self.selected_ranges
        width = x_to - x_from
        height = y_to - y_from

        if width < 128 or height < 128:
            QMessageBox.warning(self, "Area too small", "The area must be at least 128x128 pixels.")
            return

        self.accept()

    def get_selected_ranges(self):
        return self.selected_ranges if self.selected_ranges else (0, 128, 0, 128)
    
class RangeDialogAd(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Select the box to extract the noise")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
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

        self.x_from.editingFinished.connect(self.on_manual_input)
        self.y_from.editingFinished.connect(self.on_manual_input)

    def on_manual_input(self):
        try:
            x = int(self.x_from.text())
            y = int(self.y_from.text())
        except ValueError:
            return  # Ignorar si no es un número válido

        x = max(0, min(x, self.data.shape[1] - 128))
        y = max(0, min(y, self.data.shape[0] - 128))
        self.update_plot(x, y)

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
        self.canvas.ax.imshow(self.data, cmap="gray", origin="upper")

        self.rect = Rectangle((x, y), 128, 128, linewidth=2, edgecolor='cyan', facecolor='none')
        self.canvas.ax.add_patch(self.rect)
        self.canvas.draw()

        preview_data = self.data[y:y + 128, x:x + 128]
        self.preview.ax.clear()
        self.preview.ax.imshow(preview_data, cmap='gray', origin='upper')
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
    def __init__(self, parent=None, data=None,
                 iline_min=0, iline_max=0, xline_min=0, xline_max=0):
        super().__init__(parent)
        self.setWindowTitle("Select a Section")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(460, 540)
        self.setStyleSheet("QDialog { background-color: #F9FAFB; border-radius: 12px; }")

        self.data = data.copy() if data is not None else None
        self.canvas = MplCanvas(self)

        # Radios
        self.inline_radio = QRadioButton("Enhance Inline Section")
        self.xline_radio = QRadioButton("Enhance Crossline Section")
        self.inline_radio.setChecked(True)

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.inline_radio)
        self.mode_group.addButton(self.xline_radio)

        # Campos de recorte espacial
        self.x_from = QLineEdit("0")
        self.x_to = QLineEdit(str(self.data.shape[1]) if self.data is not None else "500")
        self.y_from = QLineEdit("0")
        self.y_to = QLineEdit(str(self.data.shape[0]) if self.data is not None else "500")

        # Índices de línea iniciales (usamos los valores reales directamente)
        self.iline_from = QLineEdit(str(iline_min))
        self.iline_to = QLineEdit(str(iline_max))
        self.xline_from = QLineEdit(str(xline_min))
        self.xline_to = QLineEdit(str(xline_max))

        # Layout general
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Select enhancement axis:"))
        layout.addWidget(self.inline_radio)
        layout.addLayout(self._row("Inline from:", self.iline_from, "to", self.iline_to))
        layout.addWidget(self.xline_radio)
        layout.addLayout(self._row("Xline from:", self.xline_from, "to", self.xline_to))
        layout.addSpacing(8)
        layout.addLayout(self._row("X from:", self.x_from, "to", self.x_to))
        layout.addLayout(self._row("Y from:", self.y_from, "to", self.y_to))
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

        # Conexión dinámica
        for box in [self.x_from, self.x_to, self.y_from, self.y_to]:
            box.textChanged.connect(self.update_plot)

        self.update_plot()

    def _row(self, label1, field1, label2, field2):
        row = QHBoxLayout()
        row.addWidget(QLabel(label1))
        row.addWidget(field1)
        row.addWidget(QLabel(label2))
        row.addWidget(field2)
        return row

    def get_ranges(self):
        return {
            "mode": "iline" if self.inline_radio.isChecked() else "xline",
            "x": (int(self.x_from.text()), int(self.x_to.text())),
            "y": (int(self.y_from.text()), int(self.y_to.text())),
            "iline": (int(self.iline_from.text()), int(self.iline_to.text())),
            "xline": (int(self.xline_from.text()), int(self.xline_to.text()))
        }

    def update_plot(self):
        try:
            if self.data is None:
                return
            x0 = int(self.x_from.text())
            x1 = int(self.x_to.text())
            y0 = int(self.y_from.text())
            y1 = int(self.y_to.text())
            if x1 > x0 and y1 > y0:
                cropped = self.data[y0:y1, x0:x1].T
                self.canvas.ax.clear()
                self.canvas.ax.imshow(cropped.T, cmap="gray", origin="upper", aspect="auto")
                self.canvas.draw()
        except:
            pass
