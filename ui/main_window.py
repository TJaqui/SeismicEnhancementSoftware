from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QAction, QMenuBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from ui.dialogs.select_mode_dialog import SelectModeDialog
from ui.dialogs.help_dialog import HelpDialog
from ui.dialogs.about_dialog import AboutDialog
from ui.sidebar import SideBar
from ui.toolbar import TopToolBar
from ui.display_panel import DisplayPanel


class MainWindow(QMainWindow):
    def __init__(self, mode, file_path):
        super(MainWindow, self).__init__()
        self.setWindowTitle("NED")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet("background-color: #F9FAFB;")

        # --- Estructura principal ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Crear display panel antes del toolbar para poder pasar la referencia
        self.displaypanel = DisplayPanel(self)

        # Toolbar superior con referencia al displaypanel
        self.toolbar = TopToolBar(display_panel=self.displaypanel)
        main_layout.addWidget(self.toolbar)

        # Contenido horizontal
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.sidebar = SideBar()
        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.displaypanel)

        self.displaypanel.sidebar = self.sidebar
        self.sidebar.iline_spin.valueChanged.connect(self.displaypanel.update_plot)
        self.sidebar.xline_spin.valueChanged.connect(self.displaypanel.update_plot)
        # Finalizar layout principal
        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)

        # Cargar archivo inicial
        self.displaypanel.load_file(file_path, mode)

        # Conexiones UI
        self.sidebar.view_group.buttonClicked[int].connect(self.toggle_view_mode)
        self.sidebar.hide_view_buttons()
        self.showing_enhanced = False

        self.toolbar.connect_buttons(
            self.handle_open,
            self.displaypanel.save_data,
            self.displaypanel.enhance_data,
            self.displaypanel.adapt_to_data
        )

        # Crear barra de menú
        self._create_menubar()

    def _create_menubar(self):
        menubar = QMenuBar(self)
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #F9FAFB;
                font-size: 14px;
            }
            QMenuBar::item:selected {
                background: #E6F7F5;
            }
            QMenu {
                background-color: #FFFFFF;
                color: #1E1E1E;
                font-size: 14px;
            }
            QMenu::item:selected {
                background-color: #2979FF;
                color: white;
            }
        """)

        file_menu = menubar.addMenu("File")

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.handle_open)

        save_action = QAction("Save file", self)
        save_action.triggered.connect(self.displaypanel.save_data)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(exit_action)

        about_menu = menubar.addMenu("About")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        about_menu.addAction(about_action)

        help_menu = menubar.addMenu("Help")
        help_action = QAction("Help", self)
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

        self.setMenuBar(menubar)

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
            self.displaypanel.show_seismic(self.displaypanel.data, cmap="gray")
            self.showing_enhanced = False
        elif id == 1 and self.displaypanel.dataEnhanced is not None:
            self.displaypanel.show_seismic(self.displaypanel.dataEnhanced, cmap="gray")
            self.showing_enhanced = True

    def _show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()
