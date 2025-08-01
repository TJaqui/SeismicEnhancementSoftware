from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QApplication, QMainWindow, QLabel, QHBoxLayout, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
from PyQt5.QtCore import Qt
import segyio
import traceback
import utils
import os
from ui.dialogs.range_dialog import RangeDialog
from ui.dialogs.range_dialog import RangeDialogAd
from ui.dialogs.range_dialog import RangeDialog3D
from ui.dialogs.zdialog import ZDialog
from ui.dialogs.progress_dialog import ProgressDialog
from ui.sidebar3d import SideBar3D
from finetuning import parallelTrain
from ui.view_control import ViewControl
from pathlib import Path
import matplotlib.pyplot as plt

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

        # 👉 Botón de zoom área (tipo lupa)
        self.btn_zoom_area = QPushButton("🔍 Zoom")
        self.btn_zoom_area.setCheckable(True)
        self.btn_zoom_area.setMinimumHeight(36)
        self.btn_zoom_area.setMaximumWidth(90)  # Limita el ancho máximo
        self.btn_zoom_area.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: none;
                padding: 6px 6px;
                text-align: center;
                color: #1E1E1E;
                font-size: 13px;
                font-weight: bold;
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

        # 👉 Botón reset (casita)
        self.btn_reset = QPushButton("🏠 Reset")
        self.btn_reset.setMinimumHeight(36)
        self.btn_reset.setMaximumWidth(90)  # Limita el ancho máximo
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: none;
                padding: 6px 6px;
                text-align: center;
                color: #1E1E1E;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
            }
        """)

        # 🧭 Toolbar interna de Matplotlib para usar zoom tipo lupa
        self.nav_toolbar = NavigationToolbar(self.canvas, self)
        self.nav_toolbar.setVisible(False)  # oculta visualmente, pero podemos usar sus métodos

        # 📦 Layout de botones debajo del canvas
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(12, 0, 12, 6)
        btn_layout.setSpacing(10)
        btn_layout.addWidget(self.btn_zoom_area)
        btn_layout.addWidget(self.btn_reset)

        layout.addWidget(self.canvas)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.min_label = QLabel("Min: N/A")
        self.max_label = QLabel("Max: N/A")

        # Conectar acciones
        self.btn_zoom_area.clicked.connect(self.toggle_zoom_area)
        self.btn_reset.clicked.connect(lambda: self.view_control.reset_view())

    def toggle_zoom_area(self):
        if self.btn_zoom_area.isChecked():
            self.view_control.set_pan_enabled(False)   # 🔒 Desactiva pan
            self.nav_toolbar.zoom()
        else:
            self.view_control.set_pan_enabled(True)    # 🔓 Reactiva pan
            self.nav_toolbar.zoom()

    def show_seismic(self, data, cmap=None):
        if cmap is None:
            cmap = self.current_mode

        self.canvas.ax.clear()

        # Eliminar cualquier eje adicional excepto el principal
        for ax in self.canvas.fig.axes[:]:
            if ax != self.canvas.ax:
                self.canvas.fig.delaxes(ax)

        # Mostrar la imagen sísmica
        
        #im = self.canvas.ax.imshow(data, cmap=cmap, aspect='equal', origin='upper')

        
        im = self.canvas.ax.imshow(data, cmap=cmap, aspect='auto', origin='upper', extent=self.extent)
        

        self.canvas.fig.canvas.draw_idle()

        # Print current axis limits to debug
        print("X axis limits after plotting:", self.canvas.ax.get_xlim())
        print("Y axis limits after plotting:", self.canvas.ax.get_ylim())
        # Axis labels
        filename = self.data_path.split("/")[-1] if hasattr(self, "data_path") else "Seismic Image"
        self.canvas.ax.set_title(filename, fontsize=14, fontweight='bold', color="#1E1E1E", pad=10)

        self.canvas.ax.tick_params(axis='both', colors='#4D4D4D', labelsize=9)
        # Título y etiquetas
        filename = os.path.basename(self.data_path) if hasattr(self, "data_path") else "Seismic Image"
        #filename = self.data_path.split("/")[-1] if hasattr(self, "data_path") else "Seismic Image"
        self.canvas.ax.set_title(filename, fontsize=14, fontweight='bold', color="#1E1E1E", pad=10)
        
        
        for da in data.shape:
            print("X axis label")
            print("extent", self.extent)
            print("extent", da)
            if self.extent[1] == da-1:
                
                self.canvas.ax.set_xlabel("Trace")
            else:
                self.canvas.ax.set_xlabel("Distance (m)")
            if self.extent[2] == da:
                self.canvas.ax.set_ylabel("Pixel")
            else:
                self.canvas.ax.set_ylabel("Seconds (s)")



        
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

    def show_difference(self,  line=None,mode=None):
        if self.data is not None and self.dataEnhanced is not None:
          
            #print(self.data.shape)
            #print(self.dataEnhanced.shape)
            #diff = self.data - self.dataEnhanced
            if len(self.data.shape) <=2 and len(self.dataEnhanced.shape)<=2:
                print("its in")
                diff = self.data - self.dataEnhanced
                self.show_seismic(diff, cmap=self.current_mode) 
            elif  len(self.dataEnhanced.shape) ==3:
                
                
                if mode=="inline":

                    index = line - self.inline_offset
                    diff = self.file.iline[line].T - self.dataEnhanced[index]
                    self.show_seismic(diff, cmap=self.current_mode)
                elif mode == "zslice":
                    pass
                elif mode == "crossline":
                    index = line - self.crossline_offset
                    diff = self.file.xline[line].T - self.dataEnhanced[:,:,index].T

                    self.show_seismic(diff, cmap=self.current_mode) 


    def show_current(self, line=None, mode=None):
        if self.showing_enhanced and hasattr(self, "dataEnhanced") and self.dataEnhanced is not None:
            data = self.dataEnhanced
        elif hasattr(self, "data") and self.data is not None:
            data = self.data
        else:
            print("❌ No hay datos válidos para mostrar.")
            return 

        if len(data.shape) <= 2:
            if self.current_mode == "wiggle":
                self._show_wiggle(data)
            else:
                self.show_seismic(data)

        elif len(data.shape) == 3:
            if mode == "inline":
                index = line - self.inline_offset
                if self.current_mode == "wiggle":

                    self._show_wiggle(data[index])
                else:
                    self.show_seismic(data[index])
            elif mode == "zslice":
                  
                    pass
            elif mode == "crossline":
                index = line - self.crossline_offset
                print(f"📎 Slice crossline: data[:,:,{line}].T.shape = {data[:,:,line].T.shape}")
                if self.current_mode == "wiggle":
                    self._show_wiggle(data[:,:,index].T)
                else:
                    self.show_seismic(data[:,:,index].T)
        else:
            print(f"❌ Forma de datos no soportada: {data.shape}")
            return

        self.update_min_max_labels()

    def update_plot(self):
        if not isinstance(self.sidebar, SideBar3D):
            return

        section, line_type, line_num = self.sidebar.get_active_section()
        if section is None or line_type is None:
            return

        if line_type == "inline":
            self.data = self.file.iline[line_num].T
        elif line_type == "zslice":
           pass
        elif line_type == "crossline":
            self.data = self.file.xline[line_num].T

        if section == "Original":
            self.showing_enhanced = False
            self.show_current(line_num, line_type)
        elif section == "Enhanced" and self.dataEnhanced is not None:
            self.showing_enhanced = True
            self.show_current(line_num,line_type)
        elif section == "Difference" and self.dataEnhanced is not None:
            self.show_difference(line_num,line_type)

        self.update_min_max_labels()

    def load_file(self, path, mode):
        try:
            path = Path(path) 
            print(f"\U0001F4C2 Loading file: {path} as {mode}")
            
            self.mode = mode
            self.data_path = str(path)

            if mode == "2D":
             
                self.file = segyio.open(str(path), ignore_geometry=True)

                self.data = self.file.trace.raw[:].T
                self.datamin = self.data.min()
                self.datamax = self.data.max()

                print(f"✅ Shape of 2D data: {self.data.shape}")
                self.dataEnhanced = None
                
                dt_microseconds = self.file.bin[segyio.BinField.Interval]
                dt_seconds = dt_microseconds / 1e6
                num_samples = self.data.shape[0]
                time_axis = np.arange(num_samples) * dt_seconds  # seconds

                # Distance Axis
                cdp_x = self.file.attributes(segyio.TraceField.CDP_X)[:]
                cdp_y = self.file.attributes(segyio.TraceField.CDP_Y)[:]

                # Robust check
                if np.all(cdp_x == cdp_x[0]) and np.all(cdp_y == cdp_y[0]):
                    print("⚠️ No variation in CDP coordinates, defaulting spacing to 1.")
                    spacing = 1.0
                else:
                    distances = np.sqrt((cdp_x - cdp_x[0])**2 + (cdp_y - cdp_y[0])**2)
                    unique_distances = np.unique(distances)
                    if len(unique_distances) > 1:
                        spacing = np.mean(np.diff(unique_distances))
                    else:
                        spacing = 1.0
                        print("⚠️ Insufficient variation in distances, using default spacing = 1.")

                num_traces = self.data.shape[1]
                distance_axis = np.arange(num_traces) * spacing

                # Confirm valid extent (no NaNs or Inf)
                if np.isfinite(distance_axis).all() and np.isfinite(time_axis).all():
                    self.extent = [distance_axis[0], distance_axis[-1], time_axis[-1], time_axis[0]]
                else:
                    self.extent = [0, num_traces - 1, num_samples * dt_seconds, 0]
                    print("⚠️ Invalid axes values, fallback to default indices.")
                self.show_current()

            elif mode == "3D":
                self.file = segyio.open(str(path))
                self.ilines = list(self.file.ilines)
                self.xlines = list(self.file.xlines)
                self.inline_offset = self.ilines[0]      # e.g. 100
                self.crossline_offset = self.xlines[0]
                main_window = find_main_window(self)
                if main_window and hasattr(main_window, "sidebar"):
                    main_window.sidebar.set_ixline_limits(self.ilines[0], self.ilines[-1], self.xlines[0], self.xlines[-1])

                "self.data = self.file.iline[self.ilines[0]].T"
                self.volume = np.stack([self.file.iline[i].T for i in self.ilines]) #prueba
                self.datamin = self.volume.min()
                self.datamax = self.volume.max()
                self.dataEnhanced = self.volume.copy()                              #prueba
                dt_microseconds = self.file.bin[segyio.BinField.Interval]
                dt_seconds = dt_microseconds / 1e6
                num_samples = self.data.shape[0]
                time_axis = np.arange(num_samples) * dt_seconds  # seconds

                # Distance Axis
                cdp_x = self.file.attributes(segyio.TraceField.CDP_X)[:]
                cdp_y = self.file.attributes(segyio.TraceField.CDP_Y)[:]

                # Robust check
                if np.all(cdp_x == cdp_x[0]) and np.all(cdp_y == cdp_y[0]):
                    print("⚠️ No variation in CDP coordinates, defaulting spacing to 1.")
                    spacing = 1.0
                else:
                    distances = np.sqrt((cdp_x - cdp_x[0])**2 + (cdp_y - cdp_y[0])**2)
                    unique_distances = np.unique(distances)
                    if len(unique_distances) > 1:
                        spacing = np.mean(np.diff(unique_distances))
                    else:
                        spacing = 1.0
                        print("⚠️ Insufficient variation in distances, using default spacing = 1.")

                num_traces = self.data.shape[1]
                distance_axis = np.arange(num_traces) * spacing

                # Confirm valid extent (no NaNs or Inf)
                if np.isfinite(distance_axis).all() and np.isfinite(time_axis).all():
                    self.extent = [distance_axis[0], distance_axis[-1], time_axis[-1], time_axis[0]]
                else:
                    self.extent = [0, num_traces - 1, num_samples * dt_seconds, 0]
                    print("⚠️ Invalid axes values, fallback to default indices.")
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
            self.dataEnhanced -= self.dataEnhanced.min()
            self.dataEnhanced /= self.dataEnhanced.max()
            
            self.dataEnhanced[y_start:y_end, x_start:x_end] = self.datatoEnhanced[
                top:self.datatoEnhanced.shape[0] - bot,
                lf:self.datatoEnhanced.shape[1] - rt
            ]

            self.show_current()
            progress_dialog.update_progress(100)
            progress_dialog.accept()

            self.dataEnhanced = utils.denorm_0_1_to_range(self.dataEnhanced, self.datamin, self.datamax)
            main_window = find_main_window(self)
            if main_window and hasattr(main_window, "sidebar"):
                main_window.sidebar.show_view_buttons()
                main_window.sidebar.view_original_btn.setChecked(True)

        except EnhancementCancelled:
            print("🚫 Enhancement cancelled by user.")
        except Exception as e:
            print(f"❌ Enhancement Error: {type(e).__name__}: {e}")
            traceback.print_exc()  # <--- muestra la línea exacta del error
            self._show_error("Enhancement Error", str(e))
        finally:
            if progress_dialog and progress_dialog.isVisible():
                progress_dialog.reject()

    def enhance_data_3D(self):
        progress_dialog = None
        try:
            dialog = RangeDialog3D(
                parent=self,
                data=self.data,
                iline_min=self.ilines[0],
                iline_max=self.ilines[-1],
                xline_min=self.xlines[0],
                xline_max=self.xlines[-1]
            )
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
                inline_offset = self.ilines[0]  # índice real mínimo

                for idx, i in enumerate(range(iline_from, iline_to + 1)):
                    array_index = i - inline_offset  # convertir índice real a índice de array
                    print(f"Procesando iline real={i} (índice interno={array_index})")
                    print(f"→ Accediendo self.file.iline[{i}][{y_start}:{y_end}, {x_start}:{x_end}]")

                    section = self.file.iline[i].T[y_start:y_end, x_start:x_end]
                    print(section.shape)

                    if section.size == 0:
                        raise ValueError("Selected iline section is empty.")

                    #section = (section - section.min()) / max(section.max(), 1e-6)
                    TestData, top, bot, lf, rt = utils.padding(section)
                    TestData -= TestData.min()
                    TestData /= TestData.max()  # Evitar división por cero 
                    #TestData = (TestData - TestData.min()) / max(TestData.max(), 1e-6)
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

                    print("✅ Result shape:", result.shape)
                    self.dataEnhanced[array_index][y_start:y_end, x_start:x_end] = result[
                        top:result.shape[0] - bot,
                        lf:result.shape[1] - rt
                    ]
                    self.dataEnhanced = utils.denorm_0_1_to_range(self.dataEnhanced, self.datamin, self.datamax)

            elif mode == "xline":
                print("\n▶ Procesando modo XLINE")
                total_slices = xline_to - xline_from + 1
                crossline_offset = self.xlines[0]  # índice real mínimo

                for idx, i in enumerate(range(xline_from, xline_to + 1)):
                    array_index = i - crossline_offset  # convertir índice real a índice de array
                    print(f"Procesando xline real={i} (índice interno={array_index})")
                    print(f"→ Accediendo self.file.xline[{i}].T[{x_start}:{x_end}, {y_start}:{y_end}]")

                    section = self.file.xline[i].T
                    section_crop = section[y_start:y_end,x_start:x_end]

                    if section_crop.size == 0:
                        raise ValueError("Selected Crossline section is empty.")

                    section_crop = (section_crop - section_crop.min()) / max(section_crop.max(), 1e-6)
                    TestData, top, bot, lf, rt = utils.padding(section_crop)
                    
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

                    print("✅ Result shape:", result[
                        top:result.shape[0] - bot,
                        lf:result.shape[1] - rt
                    ].shape)
                    self.dataEnhanced[x_start:x_end, y_start:y_end, array_index] = result[
                        top:result.shape[0] - bot,
                        lf:result.shape[1] - rt
                    ].T
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
            main_window = find_main_window(self)
            sidebar = main_window.sidebar
            if hasattr(sidebar, "get_active_section"):
                section, axis, line_value = sidebar.get_active_section()
                if section and axis:
                    slice_mode = axis
                    line = line_value
                    print(f"🧭 Sección activa: {section} | Modo: {slice_mode} | Línea: {line}")

                    if section == "Difference":
                        self.show_difference(line, slice_mode)
                    else:
                        self.show_current(line=line, mode=slice_mode)
            print(len(self.dataEnhanced.shape))
            if len(self.dataEnhanced.shape)<=2:
                print("Adaptando a datos 2D")
                dialog = RangeDialogAd(self, data=self.dataEnhanced)
            elif len(self.dataEnhanced.shape) == 3: 
                print("Adaptando a datos 2D")

                if  axis == "inline":
                    index = line_value - self.inline_offset
                    dialog = RangeDialogAd(self, data=self.dataEnhanced[index])  
                elif axis == "crossline":
                    index = line_value - self.crossline_offset
                    dialog = RangeDialogAd(self, data=self.dataEnhanced[:,:,index].T)  

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
        slice_mode = "inline"
        line = None

        if main_window and hasattr(main_window, "sidebar"):
            sidebar = main_window.sidebar

            # 🚧 Modo 2D
            if hasattr(sidebar, "view_group"):
                btn_id = sidebar.view_group.checkedId()
                if btn_id == 2:
                    self.show_difference()
                    return
                else:
                    self.show_current()
                    return

            # 🚀 Modo 3D
            if hasattr(sidebar, "get_active_section"):
                section, axis, line_value = sidebar.get_active_section()
                if section and axis:
                    slice_mode = axis
                    line = line_value
                    print(f"🧭 Sección activa: {section} | Modo: {slice_mode} | Línea: {line}")

                    if section == "Difference":
                        self.show_difference(line, slice_mode)
                    else:
                        self.show_current(line=line, mode=slice_mode)
                    return

        # Fallback (sin sidebar o modo desconocido)
        self.show_current(line=line, mode=slice_mode)

        
    def update_slice(self, section, axis, line_value):
    
        if axis == "inline":
            self.data = self.file.iline[line_value].T
        elif axis == "crossline":
            self.data = self.file.xline[line_value].T
        elif axis == "zslice":
            if section == "Original":
                
                dialog = ZDialog(self, data=self.volume)
                dialog.exec_()
            elif section == "Enhanced" and self.dataEnhanced is not None:
                dialog = ZDialog(self, data=self.dataEnhanced)
                dialog.exec_()
             
            elif section == "Difference" and self.dataEnhanced is not None:
                dialog = ZDialog(self, data=self.volume - self.dataEnhanced)
                dialog.exec_()

        if section == "Original":
            self.showing_enhanced = False
            self.show_current(line_value,axis)
        elif section == "Enhanced" and self.dataEnhanced is not None:
            self.showing_enhanced = True
            self.show_current(line_value, axis)
        elif section == "Difference" and self.dataEnhanced is not None:
            self.show_difference(line_value, axis)

        self.update_min_max_labels()

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
