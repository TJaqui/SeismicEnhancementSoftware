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

class EnhancementCancelled(Exception):
    """Raised when the enhancement process is cancelled by the user."""
    pass

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

        #try:
        #    xlim = self.canvas.ax.get_xlim()
        #    ylim = self.canvas.ax.get_ylim()
        #except Exception:
        #   xlim = ylim = None

        self.canvas.ax.clear()
        self.canvas.ax.imshow(data.T, cmap=cmap, aspect='equal', origin='upper')
        self.canvas.ax.tick_params(axis='both', colors='black')
        self.canvas.ax.spines['top'].set_visible(False)
        self.canvas.ax.spines['right'].set_visible(False)
        self.canvas.figure.tight_layout()

        #if xlim and ylim:
        #    self.canvas.ax.set_xlim(xlim)
        #    self.canvas.ax.set_ylim(ylim)

        self.canvas.draw()

    def update_plot(self):
        if self.sidebar.inline_btn.isChecked():
            line_num = self.sidebar.iline_spin.value()
            self.data = self.file.iline[line_num]
            self.show_seismic(self.data, cmap="gray")
        elif self.sidebar.crossline_btn.isChecked():
            line_num = self.sidebar.xline_spin.value()
            self.data = self.file.xline[line_num]
            self.show_seismic(self.data, cmap="gray")
        else:
            return
    
    def load_file(self, path, mode):
        try:
            print(f"📂 Loading file: {path} as {mode}")
            self.mode = mode
            self.data_path = path
            if mode == "2D":
                global datamin, datamax
                self.file = segyio.open(path,ignore_geometry=True)
                self.data = self.file.trace.raw[:]
                datamin =  self.data.min()
                datamax = self.data.max()
                
                self.data -= self.data.min()
                self.data /= self.data.max()
                '''
                with segyio.open(path, "r", ignore_geometry=True) as f:
                    data = np.array(f.trace.raw[:])
                '''
                print(f"✅ Shape of 2D data: {self.data.shape}")
                                   
                self.dataEnhanced = None
                self.show_seismic(self.data, cmap="gray")
            elif mode == "3D":
                '''
                with segyio.open(path, "r") as f:
                    f.mmap()
                    cube = segyio.tools.cube(f)
                    print(f"✅ Shape of 3D cube: {cube.shape}")
                    middle_slice = cube.shape[0] // 2
                    data = cube[middle_slice, :, :]
                    self.data = data                    
                    self.dataEnhanced = None
                    self.show_seismic(data, cmap="gray")
                '''
                #global datamin, datamax

                self.file = segyio.open(path)
                self.ilines = list(self.file.ilines)
                self.xlines = list(self.file.xlines)

                main_window = find_main_window(self)
                if main_window and hasattr(main_window, "sidebar"):
                    main_window.sidebar.set_ixline_limits(self.ilines[0],self.ilines[-1],self.xlines[0],self.xlines[-1])
                    
                self.data = self.file.iline[self.ilines[0]]
                self.show_seismic(self.data, cmap="gray")

        except Exception as e:
            print(f"❌ Failed to load seismic data: {e}")
            self.canvas.draw_empty()

    def enhance_data(self):
        progress_dialog = None
        try:
            dialog = RangeDialog(self, data=self.data)
            if dialog.exec_() != dialog.Accepted:
                return

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

            def safe_update(value, msg=""):
                if progress_dialog.is_cancelled():
                    raise EnhancementCancelled()
                progress_dialog.update_progress(value, msg)

            self.datatoEnhanced = utils.seismicEnhancement(
                patches,
                TestData.shape,
                progress_callback=safe_update
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

        except EnhancementCancelled:
            print("🚫 Enhancement cancelled by user.")
        except Exception as e:
            print(f"❌ Enhancement Error: {e}")
            self._show_error("Enhancement Error", str(e))
        finally:
            if progress_dialog and progress_dialog.isVisible():
                progress_dialog.reject()

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

    def _show_error(self, title, message):
        error_dialog = QMessageBox(self)
        error_dialog.setWindowTitle(title)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setText(message)
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()

    def _show_wiggle(self, data):

        #try:
        #    xlim = self.canvas.ax.get_xlim()
        #    ylim = self.canvas.ax.get_ylim()
        #except Exception:
        #    xlim = ylim = None
    
        self.canvas.ax.clear()
        for i in range(data.shape[1]):
            trace = data.T[:, i]
            norm_trace = trace / np.max(np.abs(trace))
            self.canvas.ax.plot(norm_trace + i, range(len(trace)), color="black", linewidth=0.2)
        self.canvas.ax.invert_yaxis()

        #if xlim and ylim:
        #    self.canvas.ax.set_xlim(xlim)
        #    self.canvas.ax.set_ylim(ylim)

        self.canvas.draw()

    def set_visualization_mode(self, mode):
        if not hasattr(self, "data") and not hasattr(self, "dataEnhanced"):
            print("No hay datos cargados aún.")
            return

        # Asegurar que al menos uno exista antes de usar
        if hasattr(self, "dataEnhanced") and self.dataEnhanced is not None:
            data = self.dataEnhanced
        elif hasattr(self, "data") and self.data is not None:
            data = self.data
        else:
            print("No hay datos válidos para mostrar.")
            return

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
        self.fig = Figure(facecolor='white')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('white')
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)

        self.draw_empty()

        self.mpl_connect("scroll_event", self._on_scroll)

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

    def _on_scroll(self, event):
        base_scale = 1.2
        xdata, ydata = event.xdata, event.ydata
        if xdata is None or ydata is None:
            return

        scale_factor = 1 / base_scale if event.button == 'up' else base_scale

        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        new_xlim = [
            xdata - (xdata - cur_xlim[0]) * scale_factor,
            xdata + (cur_xlim[1] - xdata) * scale_factor
        ]
        new_ylim = [
            ydata - (ydata - cur_ylim[0]) * scale_factor,
            ydata + (cur_ylim[1] - ydata) * scale_factor
        ]

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.draw()
