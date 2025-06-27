from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QMessageBox, QApplication, QMainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import segyio
import time
import utils
from ui.dialogs.range_dialog import RangeDialog
from ui.dialogs.range_dialog import RangeDialogAd
from ui.dialogs.progress_dialog import ProgressDialog
from finetuning import parallelTrain

class DisplayPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.canvas = MplCanvas(self)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def show_seismic(self, data, cmap="gray"):
        self.canvas.ax.clear()
        self.canvas.ax.imshow(data.T, cmap=cmap, aspect='equal', origin='upper')
        self.canvas.ax.tick_params(axis='both', colors='black')
        self.canvas.ax.spines['top'].set_visible(False)
        self.canvas.ax.spines['right'].set_visible(False)
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def load_file(self, path, mode):
        try:
            print(f"📂 Loading file: {path} as {mode}")
            self.mode = mode
            if mode == "2D":
                with segyio.open(path, "r", ignore_geometry=True) as f:
                    data = np.array(f.trace.raw[:])
                    print(f"✅ Shape of 2D data: {data.shape}")
                    self.data = data                    
                    self.dataEnhanced = None
                    self.show_seismic(data, cmap="gray")
            elif mode == "3D":
                with segyio.open(path, "r", ignore_geometry=True) as f:
                    f.mmap()
                    cube = segyio.tools.cube(f)
                    print(f"✅ Shape of 3D cube: {cube.shape}")
                    middle_slice = cube.shape[0] // 2
                    data = cube[middle_slice, :, :]
                    self.data = data                    
                    self.dataEnhanced = None
                    self.show_seismic(data, cmap="gray")
        except Exception as e:
            print(f"❌ Failed to load seismic data: {e}")
            self.canvas.draw_empty()

    def enhance_data(self):
        try:
            dialog = RangeDialog(self, data=self.data)
            if dialog.exec_() == dialog.Accepted:
                x_start, x_end, y_start, y_end = dialog.get_ranges()

                progress_dialog = ProgressDialog("Enhancing Data", self)
                progress_dialog.label.setText("Enhancing...")
                progress_dialog.show()
                QApplication.processEvents()

                self.dataEnhanced = self.data.copy()
                datato_enhance = self.data[y_start:y_end, x_start:x_end]

                TestData, top, bot, lf, rt = utils.padding(datato_enhance)
                TestData -= TestData.min()
                TestData /= TestData.max()
                patches = utils.patchDivision(TestData)

                self.datatoEnhanced = utils.seismicEnhancement(
                    patches,
                    TestData.shape,
                    progress_callback=progress_dialog.update_progress
                )

                self.dataEnhanced[y_start:y_end, x_start:x_end] = self.datatoEnhanced[
                    top:self.datatoEnhanced.shape[0] - bot,
                    lf:self.datatoEnhanced.shape[1] - rt
                ]

                self.show_seismic(self.dataEnhanced, cmap="gray")
                progress_dialog.update_progress(100)
                progress_dialog.accept()

                main_window = find_main_window(self)
                if main_window and hasattr(main_window, "sidebar"):
                    main_window.sidebar.show_view_buttons()
                    main_window.sidebar.view_enhanced_btn.setChecked(True)

        except Exception as e:
            print(f"❌ Enhancement Error: {e}")
            self._show_error("Enhancement Error", str(e))

    def adapt_to_data(self):
        try:
            dialog = RangeDialogAd(self, data=self.data)
            if dialog.exec_() == dialog.Accepted:
                x_start, x_end, y_start, y_end = dialog.get_ranges()
                batch_size, iterations, epochs, gen_samples = dialog.get_ranges()
                cropped = self.data[y_start:y_end, x_start:x_end]
                self.show_seismic(cropped, cmap="gray")
                parallelTrain(cropped, batch_size, epochs, iterations, gen_samples)
        except Exception as e:
            self._show_error("Adaptation Error", str(e))

    def save_data(self):
        try:
            dname = QFileDialog.getExistingDirectory(self, 'Save directory', 'C:/')
            if dname:
                utils.save2dData(self.dataEnhanced, "seismic.sgy", dname, self.data.min(), self.data.max())
        except Exception as e:
            self._show_error("Save Error", str(e))

    def _show_error(self, title, message):
        error_dialog = QMessageBox(self)
        error_dialog.setWindowTitle(title)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setText(message)
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()

    def _show_wiggle(self, data):
        self.canvas.ax.clear()
        for i in range(data.shape[1]):
            trace = data[:, i]
            norm_trace = trace / np.max(np.abs(trace))
            self.canvas.ax.plot(norm_trace + i, range(len(trace)), color="black", linewidth=0.5)
        self.canvas.ax.invert_yaxis()
        self.canvas.ax.set_title("Wiggle Plot")
        self.canvas.draw()

    def set_visualization_mode(self, mode):

        if not hasattr(self, "data") and not hasattr(self, "dataEnhanced"):
            print("No hay datos cargados aún.")
            return

        data = self.dataEnhanced if self.dataEnhanced is not None else self.data

        if mode == "seismic":
            self.show_seismic(data, cmap="seismic")
        elif mode == "gray":
            self.show_seismic(data, cmap="gray")
        elif mode == "wiggle":
            self._show_wiggle(data)
        else:
            print(f"Modo desconocido: {mode}")


def find_main_window(widget):
    while widget:
        if isinstance(widget, QMainWindow):
            return widget
        widget = widget.parent()
    return None


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(facecolor='white')
        self.ax = fig.add_subplot(111)
        self.ax.set_facecolor('white')
        super(MplCanvas, self).__init__(fig)
        self.setParent(parent)
        self.draw_empty()

    def draw_empty(self):
        self.ax.clear()
        self.ax.set_facecolor('white')
        self.ax.text(
            0.5, 0.5,
            'Visualización sísmica',
            color='gray',
            ha='center',
            va='center',
            fontsize=14,
            alpha=0.6
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.axis('off')
        self.draw()
