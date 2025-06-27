from PyQt5.QtWidgets import QStackedWidget
from PyQt5.QtGui import QIcon
from ui.start_screen import StartScreen
from ui.main_window import MainWindow
from ui.dialogs.select_mode_dialog import SelectModeDialog

class App(QStackedWidget):
    def __init__(self):
        super(App, self).__init__()

        self.setWindowIcon(QIcon("resources/logo.png"))
        self.setWindowTitle("NED")
        self.resize(1200, 800)

        self.start_screen = StartScreen(self.handle_open)
        self.main_window = None

        self.addWidget(self.start_screen)
        self.setCurrentWidget(self.start_screen)

    def handle_open(self):
        dialog = SelectModeDialog(self)
        if dialog.exec_():
            mode = dialog.get_mode()
            file_path = dialog.get_file_path()

            if file_path:
                self.main_window = MainWindow(mode=mode, file_path=file_path)
                self.addWidget(self.main_window)
                self.setCurrentWidget(self.main_window)
                if mode == "3D":
                    self.main_window.sidebar.show_3d_options()
                else:
                    self.main_window.sidebar.hide_3d_options()
            else:
                print("⚠️ No file selected.")

