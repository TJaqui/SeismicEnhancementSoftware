from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.help_dialog import HelpDialog
from ui.dialogs.save_data_dialog import SaveDataDialog

class DropDownMenuIcon(QWidget):
    def __init__(self, icon_path, title, options, callback):
        super().__init__()

        self.callback = callback
        self.options = options

        self.button = QPushButton()
        self.button.setIcon(QIcon(icon_path))
        self.button.setIconSize(QSize(48, 48))
        self.button.setFixedSize(60, 60)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #1E1E1E;
                border: 2px solid #D9D9D9;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
                border: 2px solid #B0B0B0;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
                border: 2px solid #AAAAAA;
            }
        """)

        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 14px; font-weight: 500; color: #1E1E1E;")

        self.menu_widget = QFrame()
        self.menu_widget.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D9D9D9;")
        menu_layout = QVBoxLayout()
        menu_layout.setContentsMargins(0, 0, 0, 0)

        self.buttons = {}
        for text, icon in options:
            btn = QPushButton(text)
            btn.setIcon(QIcon(icon))
            btn.setIconSize(QSize(20, 20))
            btn.setStyleSheet(self._default_style())
            btn.clicked.connect(self._make_callback(text))
            self.buttons[text] = btn
            menu_layout.addWidget(btn)

        self.menu_widget.setLayout(menu_layout)
        self.menu_widget.setWindowFlags(Qt.Popup)
        self.menu_widget.setVisible(False)

        self.button.clicked.connect(self.show_menu)

        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(6)
        v_layout.setAlignment(Qt.AlignCenter)
        v_layout.addWidget(self.button)
        v_layout.addWidget(label)

        self.setLayout(v_layout)

    def show_menu(self):
        pos = self.button.mapToGlobal(self.button.rect().bottomLeft())
        self.menu_widget.move(pos)
        self.menu_widget.adjustSize()
        self.menu_widget.show()

    def _make_callback(self, option):
        return lambda: self.callback(option)

    def _default_style(self):
        return """
            QPushButton {
                padding: 6px 12px;
                background-color: #FFFFFF;
                text-align: left;
                border: none;
                color: #1E1E1E;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
            }
        """

    def _active_style(self):
        return """
            QPushButton {
                padding: 6px 12px;
                background-color: #04BFAD;
                text-align: left;
                border: none;
                color: white;
            }
        """


class TopToolBar(QWidget):
    def __init__(self, parent=None, display_panel=None, mode="2D"):
        super(TopToolBar, self).__init__(parent)
        self.display_panel = display_panel
        self.mode = mode
        self.current_visualization = None

        outer_layout = QHBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.setAlignment(Qt.AlignLeft)

        layout = QHBoxLayout()
        layout.setContentsMargins(30, 6, 30, 6)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignLeft)

        self.openButton = self._create_button("resources/icons/open.png", "Open")
        self.saveButton = self._create_button("resources/icons/save.png", "Save")
        self.enhanceButton = self._create_button("resources/icons/enhance.png", "Enhance")
        self.adaptButton = self._create_button("resources/icons/adapt.png", "Adapt")
        self.aboutButton = self._create_button("resources/icons/about.png", "About")
        self.helpButton = self._create_button("resources/icons/help.png", "Help")

        layout.addWidget(self.openButton)
        layout.addWidget(self.saveButton)
        layout.addWidget(self.enhanceButton)
        layout.addWidget(self.adaptButton)

        self.visualizationMenu = DropDownMenuIcon(
            "resources/icons/visualization.png",
            "View",
            [
                ("Seismic", "resources/icons/seismic.png"),
                ("Gray", "resources/icons/gray.png"),
                ("Wiggle", "resources/icons/wiggle.png")
            ],
            self.handle_visualization
        )
        layout.addWidget(self.visualizationMenu)

        layout.addWidget(self.aboutButton)
        layout.addWidget(self.helpButton)

        self.visualization_buttons = self.visualizationMenu.buttons
        self.visualization_buttons["Seismic"].clicked.connect(lambda: self.set_visualization_mode("seismic"))
        self.visualization_buttons["Gray"].clicked.connect(lambda: self.set_visualization_mode("gray"))
        self.visualization_buttons["Wiggle"].clicked.connect(lambda: self.set_visualization_mode("wiggle"))

        container = QWidget()
        container.setLayout(layout)
        outer_layout.addWidget(container)
        self.setLayout(outer_layout)

    def _create_button(self, icon_path, text):
        button = QPushButton()
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(48, 48))
        button.setFixedSize(60, 60)
        button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #1E1E1E;
                border: 2px solid #D9D9D9;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
                border: 2px solid #B0B0B0;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
                border: 2px solid #AAAAAA;
            }
        """)

        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 14px; font-weight: 500; color: #1E1E1E;")

        container = QWidget()
        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(6)
        v_layout.setAlignment(Qt.AlignCenter)
        v_layout.addWidget(button)
        v_layout.addWidget(label)
        container.setLayout(v_layout)
        container.button = button
        return container

    def connect_buttons(self, on_open, on_save, on_enhance, on_adapt, on_about, on_help):
        self.openButton.button.clicked.connect(on_open)
        self.saveButton.button.clicked.connect(on_save)
        self.enhanceButton.button.clicked.connect(on_enhance)
        self.adaptButton.button.clicked.connect(on_adapt)
        self.aboutButton.button.clicked.connect(on_about)
        self.helpButton.button.clicked.connect(on_help)

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()

    def _show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def _show_dialog_dave_data(self):
        dialog = SaveDataDialog(self)
        dialog.exec_()


    def handle_visualization(self, option):
        # Este método solo reenvía el texto al nombre correcto
        self.set_visualization_mode(option.lower())

    def set_visualization_mode(self, mode):
        if self.display_panel is None:
            print("❌ No DisplayPanel conectado.")
            return

        # Resetear estilo anterior
        if self.current_visualization:
            prev_btn = self.visualization_buttons.get(self.current_visualization)
            if prev_btn:
                prev_btn.setStyleSheet(self.visualizationMenu._default_style())

        # Activar nuevo botón visual
        capitalized = mode.capitalize()
        new_btn = self.visualization_buttons.get(capitalized)
        if new_btn:
            new_btn.setStyleSheet(self.visualizationMenu._active_style())
            self.current_visualization = capitalized

        print(f"[Toolbar] Visualización → {mode}")
        self.display_panel.set_visualization_mode(mode)
