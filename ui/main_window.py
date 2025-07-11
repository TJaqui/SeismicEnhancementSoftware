from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from ui.dialogs.select_mode_dialog import SelectModeDialog
from ui.dialogs.help_dialog import HelpDialog
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.save_data_dialog import SaveDataDialog
from ui.sidebar import SideBar
from ui.sidebar3d import SideBar3D
from ui.toolbar import TopToolBar
from ui.display_panel import DisplayPanel


class MainWindow(QMainWindow):
    def __init__(self, mode, file_path):
        super(MainWindow, self).__init__()
        self.setWindowTitle("NED")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet("background-color: #F9FAFB;")
        self.mode = mode  
        # --- Estructura principal ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Crear display panel antes del toolbar para poder pasar la referencia
        self.displaypanel = DisplayPanel(self)

        # Toolbar superior con referencia al displaypanel
        self.toolbar = TopToolBar(display_panel=self.displaypanel, mode=self.mode)
        main_layout.addWidget(self.toolbar)

        # Contenido horizontal
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        if self.mode == "3D":
            self.sidebar = SideBar3D()
            self.sidebar.connect_spinboxes(self.displaypanel.update_plot)
        else:
            self.sidebar = SideBar()

        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.displaypanel)
        self.displaypanel.sidebar = self.sidebar

        # Finalizar layout principal
        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)

        # Cargar archivo inicial
        self.displaypanel.load_file(file_path, mode)

        # Conexiones UI
        if isinstance(self.sidebar, SideBar):
            self.sidebar.view_group.buttonClicked[int].connect(self.toggle_view_mode)
            self.sidebar.hide_view_buttons()

        self.showing_enhanced = False

        self.toolbar.connect_buttons(
            self.handle_open,
            self._show_dialog_save_data,
            self.handle_enhance,
            self.displaypanel.adapt_to_data,
            self._show_about,
            self._show_help
        )
    def handle_enhance(self):
        if self.mode == "2D":
            self.displaypanel.enhance_data()
        else:
            self.displaypanel.enhance_data_3D()

    def handle_open(self):
        dialog = SelectModeDialog(self)
        if dialog.exec_() == dialog.Accepted:
            file_path = dialog.get_file_path()
            mode = dialog.get_mode()

            # Quitar el sidebar anterior del layout
            self.centralWidget().layout().itemAt(1).layout().removeWidget(self.sidebar)
            self.sidebar.setParent(None)

            # Crear el nuevo sidebar según el modo
            if mode == "3D":
                from ui.sidebar3d import SideBar3D
                self.sidebar = SideBar3D()
                self.sidebar.connect_spinboxes(self.displaypanel.update_plot)
            else:
                self.sidebar = SideBar()
                self.sidebar.iline_spin.valueChanged.connect(self.displaypanel.update_plot)
                self.sidebar.xline_spin.valueChanged.connect(self.displaypanel.update_plot)

            # Añadir nuevo sidebar al layout
            self.centralWidget().layout().itemAt(1).insertWidget(0, self.sidebar)

            # Reconectar referencias
            self.displaypanel.sidebar = self.sidebar

            # Reconectar view_group si aplica
            if hasattr(self.sidebar, "view_group"):
                self.sidebar.view_group.buttonClicked[int].connect(self.toggle_view_mode)

            # Cargar el nuevo archivo
            self.mode = mode
            self.displaypanel.load_file(file_path, mode)

    def change_colormap(self, id):
        if self.displaypanel.data is not None:
            colors = ["seismic", "gray", "hot"]
            cmap = colors[id]
            self.displaypanel.show_seismic(self.displaypanel.data, cmap=cmap)

    def handle_open(self):
        dialog = SelectModeDialog(self)
        if dialog.exec_() == dialog.Accepted:
            file_path = dialog.get_file_path()
            mode = dialog.get_mode()
            self.displaypanel.load_file(file_path, mode)
            if mode == "3D":
                self.sidebar.show_3d_options()
            else:
                self.sidebar.hide_3d_options()

    def toggle_view_mode(self, id):
        if id == 0 and self.displaypanel.data is not None:
            self.displaypanel.showing_enhanced = False
            self.displaypanel.show_current()
        elif id == 1 and self.displaypanel.dataEnhanced is not None:
            self.displaypanel.showing_enhanced = True
            self.displaypanel.show_current()
        elif id == 2 and self.displaypanel.dataEnhanced is not None:
            self.displaypanel.show_difference()

    def _show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()

    def _show_dialog_save_data(self):
        if not self.displaypanel or self.displaypanel.data is None:
            return

        data = self.displaypanel.data
        dataEnhanced = self.displaypanel.dataEnhanced
        data_name = self.displaypanel.file._filename 
        mode = self.displaypanel.mode

        dialog = SaveDataDialog(
            data=data,
            dataEnhanced=dataEnhanced,
            data_name=data_name,
            mode=mode,
            parent=self
        )
        dialog.exec_()
