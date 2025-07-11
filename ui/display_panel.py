from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QApplication, QMainWindow, QLabel, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
from PyQt5.QtCore import Qt
import segyio
import utils
from ui.dialogs.range_dialog import RangeDialog
from ui.dialogs.range_dialog import RangeDialogAd
from ui.dialogs.range_dialog import RangeDialog3D
from ui.dialogs.progress_dialog import ProgressDialog
from ui.sidebar3d import SideBar3D
from finetuning import parallelTrain
from ui.view_control import ViewControl
from pathlib import Path

class EnhancementCancelled(Exception):
    pass

class DisplayPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.showing_enhanced = False 
        self.current_mode = "gray"
        self.canvas = MplCanvas(self)
        self.view_control = ViewControl(self.canvas)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.min_label = QLabel("Min: N/A")
        self.max_label = QLabel("Max: N/A")
    def show_seismic(self, data, cmap=None):
        if cmap is None:
            cmap = self.current_mode

        self.canvas.ax.clear()

        # Eliminar cualquier eje adicional excepto el principal
        for ax in self.canvas.fig.axes[:]:
            if ax != self.canvas.ax:
                self.canvas.fig.delaxes(ax)

        # Mostrar la imagen sísmica
        
        im = self.canvas.ax.imshow(data, cmap=cmap, aspect='equal', origin='upper')

        # Título y etiquetas
        filename = self.data_path.split("/")[-1] if hasattr(self, "data_path") else "Seismic Image"
        self.canvas.ax.set_title(filename, fontsize=14, fontweight='bold', color="#1E1E1E", pad=10)
        self.canvas.ax.set_xlabel("Trace", fontsize=11, color="#4D4D4D")
        self.canvas.ax.set_ylabel("Depth", fontsize=11, color="#4D4D4D")
        self.canvas.ax.tick_params(axis='both', colors='#4D4D4D', labelsize=9)
        self.canvas.ax.spines['top'].set_visible(False)
        self.canvas.ax.spines['right'].set_visible(False)

        # Añadir colorbar sin afectar layout global
        divider = make_axes_locatable(self.canvas.ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = self.canvas.fig.colorbar(im, cax=cax)
        cbar.set_label("Amplitude", fontsize=9, color="#4D4D4D")
        cbar.ax.tick_params(labelsize=8, color="#4D4D4D")

        # Restaurar vista
        self.view_control.store_original_view()
        self.view_control.restore_view()

        # Dibujar
        self.canvas.draw()

    def show_difference(self):
        if self.data is not None and self.dataEnhanced is not None:
            diff = self.data - self.dataEnhanced
            self.show_seismic(diff, cmap=self.current_mode) 

    def show_current(self, line=None,mode=None):
        if self.showing_enhanced and hasattr(self, "dataEnhanced") and self.dataEnhanced is not None:
            data = self.dataEnhanced
        elif hasattr(self, "data") and self.data is not None:
            data = self.data
        else:
            print("No hay datos válidos para mostrar.")
            return
        
        
        if len(data.shape) <=2:
            if self.current_mode == "wiggle":
                self._show_wiggle(data)
            else:
                self.show_seismic(data)
                
        
        elif len(data.shape) ==3:
            if mode=="inline":
                if self.current_mode == "wiggle":
                    self._show_wiggle(data[line])
                else:
                    self.show_seismic(data[line])
                   
            else:
                if self.current_mode == "wiggle":
                    self._show_wiggle(data[:,:,line].T)
                else:
                    self.show_seismic(data[:,:,line].T)
                  
                

        self.update_min_max_labels()

    def update_plot(self):
        if not isinstance(self.sidebar, SideBar3D):
            return

        section, line_type, line_num = self.sidebar.get_active_section()
        if section is None or line_type is None:
            return

        if line_type == "inline":
            self.data = self.file.iline[line_num].T
        else:
            self.data = self.file.xline[line_num].T

        if section == "Original":
            self.showing_enhanced = False
            self.show_current()
        elif section == "Enhanced" and self.dataEnhanced is not None:
            self.showing_enhanced = True
            self.show_current(line_num,line_type)
        elif section == "Difference" and self.dataEnhanced is not None:
            self.show_difference()

        self.update_min_max_labels()

    def load_file(self, path, mode):
        try:
            path = Path(path) 
            print(f"\U0001F4C2 Loading file: {path} as {mode}")
            
            self.mode = mode
            self.data_path = str(path)

            if mode == "2D":
                global datamin, datamax
                self.file = segyio.open(str(path), ignore_geometry=True)
                self.data = self.file.trace.raw[:].T
                datamin = self.data.min()
                datamax = self.data.max()

                self.data -= self.data.min()
                self.data /= self.data.max()
                print(f"✅ Shape of 2D data: {self.data.shape}")
                self.dataEnhanced = None
                self.show_current()

            elif mode == "3D":
                self.file = segyio.open(str(path))
                self.ilines = list(self.file.ilines)
                self.xlines = list(self.file.xlines)

                main_window = find_main_window(self)
                if main_window and hasattr(main_window, "sidebar"):
                    main_window.sidebar.set_ixline_limits(self.ilines[0], self.ilines[-1], self.xlines[0], self.xlines[-1])

                "self.data = self.file.iline[self.ilines[0]].T"
                self.volume = np.stack([self.file.iline[i].T for i in self.ilines]) #prueba
                self.dataEnhanced = self.volume.copy()                              #prueba
                self.show_current()

        except Exception as e:
            print(f"❌ Failed to load seismic data: {e}")
            self.canvas.draw_empty()

    def update_min_max_labels(self):
        if self.current_mode == "difference" and self.dataEnhanced is not None:
            data_diff = self.dataEnhanced - self.data
            data_min = data_diff.min()
            data_max = data_diff.max()
        elif self.showing_enhanced and self.dataEnhanced is not None:
            data_min = self.dataEnhanced.min()
            data_max = self.dataEnhanced.max()
        else:
            data_min = self.data.min() if self.data is not None else None
            data_max = self.data.max() if self.data is not None else None

        if data_min is not None and data_max is not None:
            self.min_label.setText(f"Min: {data_min:.2f}")
            self.max_label.setText(f"Max: {data_max:.2f}")
        else:
            self.min_label.setText("Min: N/A")
            self.max_label.setText("Max: N/A")

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

            self.show_current()
            progress_dialog.update_progress(100)
            progress_dialog.accept()

            main_window = find_main_window(self)
            if main_window and hasattr(main_window, "sidebar"):
                main_window.sidebar.show_view_buttons()
                main_window.sidebar.view_original_btn.setChecked(True)

        except EnhancementCancelled:
            print("🚫 Enhancement cancelled by user.")
        except Exception as e:
            print(f"❌ Enhancement Error: {e}")
            self._show_error("Enhancement Error", str(e))
        finally:
            if progress_dialog and progress_dialog.isVisible():
                progress_dialog.reject()

    def enhance_data_3D(self):
        progress_dialog = None
        try:
            dialog = RangeDialog3D(self, data=self.data)
            if dialog.exec_() != dialog.Accepted:
                return

            # Obtener rangos desde el diálogo
            ranges = dialog.get_ranges()
            x_start, x_end = ranges["x"]
            y_start, y_end = ranges["y"]
            iline_from, iline_to = ranges["iline"]
            xline_from, xline_to = ranges["xline"]
            mode = ranges["mode"]  # "iline" o "xline"

            shape = self.data.shape  # (n_ilines, n_samples, n_xlines)

            # 🔍 Print para verificar rangos y shape
            print("\n🔍 VALIDACIÓN DE RANGOS")
            print("Shape del volumen:", shape)
            print("Modo:", mode)
            print("X range:", x_start, x_end)
            print("Y range:", y_start, y_end)
            print("Inline range:", iline_from, iline_to)
            print("Xline range:", xline_from, xline_to)

            #self.dataEnhanced = self.file

            progress_dialog = ProgressDialog("Enhancing Data", self)
            progress_dialog.label.setText("Enhancing...")
            progress_dialog.show()
            QApplication.processEvents()

            # --- PROCESAMIENTO ---
            if mode == "iline":
                print("\n▶ Procesando modo ILINE")
                total_slices = iline_to - iline_from + 1
                for idx, i in enumerate(range(iline_from, iline_to + 1)):
                    print(f"Procesando iline {i}")
                    print(f"→ Accediendo self.file.iline[{i}][{y_start}:{y_end}, {x_start}:{x_end}]")
                    section = self.file.iline[i].T[y_start:y_end, x_start:x_end]
                    print(section.shape)
                    if section.size == 0:
                        raise ValueError("Selected iline section is empty.")
                    section = (section - section.min()) / max(section.max(), 1e-6)

                    TestData, top, bot, lf, rt = utils.padding(section)
                    TestData = (TestData - TestData.min()) / max(TestData.max(), 1e-6)
                    patches = utils.patchDivision(TestData)

                    def safe_update(value, msg=""):
                        if progress_dialog.is_cancelled():
                            raise EnhancementCancelled()
                        progress_dialog.update_progress(value, f"{msg}\n({idx+1}/{total_slices})")

                    result = utils.seismicEnhancement(
                        patches,
                        TestData.shape,
                        progress_callback=safe_update
                    )
                    print("✅ Result type:", type(result))
                    print("✅ Result shape:", getattr(result, "shape", "No shape"))
                    print("✅ Result content:", result)
                    self.dataEnhanced[i][y_start:y_end, x_start:x_end] = result[
                        top:result.shape[0] - bot,
                        lf:result.shape[1] - rt
                    ]

            elif mode == "xline":
                print("\n▶ Procesando modo XLINE")
                total_slices = xline_to - xline_from + 1
                for idx, i in enumerate(range(xline_from, xline_to + 1)):
                    print(f"Procesando xline {i}")
                    print(f"→ Accediendo self.file.xline[:, {y_start}:{y_end}, {i}]")
                    section = self.file.xline[i].T[:, y_start:y_end, i]
                    if section.size == 0:
                        raise ValueError("Selected Crossline section is empty.")
                    section = (section - section.min()) / max(section.max(), 1e-6)

                    TestData, top, bot, lf, rt = utils.padding(section)
                    TestData = (TestData - TestData.min()) / max(TestData.max(), 1e-6)
                    patches = utils.patchDivision(TestData)

                    def safe_update(value, msg=""):
                        if progress_dialog.is_cancelled():
                            raise EnhancementCancelled()
                        progress_dialog.update_progress(value, f"{msg}\n({idx+1}/{total_slices})")

                    result = utils.seismicEnhancement(
                        patches,
                        TestData.shape,
                        progress_callback=safe_update
                    )

                    self.dataEnhanced[:, y_start:y_end, i] = result[
                        top:result.shape[0] - bot,
                        lf:result.shape[1] - rt
                    ]
            self.data = self.dataEnhanced[i]
            self.show_current()
            progress_dialog.update_progress(100)
            progress_dialog.accept()

            main_window = find_main_window(self)
            if main_window and hasattr(main_window, "sidebar"):
                main_window.sidebar.show_enhanced_and_difference()

        except EnhancementCancelled:
            print("🚫 Enhancement cancelled by user.")
        except Exception as e:
            print(f"❌ Enhancement Error: {e}")
            import traceback
            traceback.print_exc()
            self._show_error("Enhancement Error", str(e))
        finally:
            if progress_dialog and progress_dialog.isVisible():
                progress_dialog.reject()

    def adapt_to_data(self):
        progress_dialog = None
        try:
            dialog = RangeDialogAd(self, data=self.data)
            if dialog.exec_() != dialog.Accepted:
                return

            x_start, x_end, y_start, y_end = dialog.get_ranges()
            batch_size, iterations, epochs, gen_samples = dialog.get_train_data()
            cropped = self.data[y_start:y_end, x_start:x_end]

            # Mostrar barra de progreso
            progress_dialog = ProgressDialog("Adapting to Data", self)
            progress_dialog.label.setText("Adapting...")
            progress_dialog.show()
            QApplication.processEvents()

            def safe_update(value, msg=""):
                if progress_dialog.is_cancelled():
                    raise EnhancementCancelled()
                progress_dialog.update_progress(value, msg)

            # Entrenamiento
            parallelTrain(cropped, batch_size, epochs, iterations, gen_samples, progress_callback=safe_update)

            progress_dialog.update_progress(100)
            progress_dialog.accept()

        except EnhancementCancelled:
            print("🚫 Adaptation cancelled by user.")
        except Exception as e:
            print(f"❌ Adaptation Error: {e}")
            self._show_error("Adaptation Error", str(e))
        finally:
            if progress_dialog and progress_dialog.isVisible():
                progress_dialog.reject()

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
            self.canvas.ax.plot(norm_trace + i, range(len(trace)), color="black", linewidth=0.2)
        self.canvas.ax.invert_yaxis()

        filename = self.data_path.split("/")[-1] if hasattr(self, "data_path") else "Seismic Wiggle"

        self.canvas.ax.set_title(filename, fontsize=14, fontweight='bold', color="#1E1E1E", pad=10)
        self.canvas.ax.set_xlabel("Trace", fontsize=11, color="#4D4D4D")
        self.canvas.ax.set_ylabel("Depth", fontsize=11, color="#4D4D4D")
        self.canvas.ax.tick_params(axis='both', colors='#4D4D4D', labelsize=9)

        self.view_control.store_original_view()
        self.view_control.restore_view()
        self.canvas.draw()

    def set_visualization_mode(self, mode):
        if not hasattr(self, "data") or self.data is None:
            print("No hay datos cargados aún.")
            return

        self.current_mode = mode

        main_window = find_main_window(self)
        if main_window and hasattr(main_window, "sidebar"):
            if hasattr(main_window.sidebar, "view_group"):
                # Modo 2D
                btn_id = main_window.sidebar.view_group.checkedId()
                if btn_id == 2:
                    self.show_difference()
                else:
                    self.show_current()
            else:
                # Modo 3D: simplemente refresca la vista
                self.show_current()
        else:
            self.show_current()


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
