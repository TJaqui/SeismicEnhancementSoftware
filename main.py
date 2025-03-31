import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QVBoxLayout
from PyQt5.uic import loadUi
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import segyio
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)  # Single subplot
        super().__init__(fig)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('seismicaplication.ui', self)  # Pasamos self para enlazar los elementos de la UI
        self.canvas = MplCanvas(self)

        # Add canvas to a layout inside the main window
        self.layout = QVBoxLayout(self.centralwidget)  # Ensure `centralwidget` is in the UI
        #self.layout.addWidget(self.canvas)
        self.canvas.setFixedSize(500, 300)
        self.openfile.clicked.connect(self.browsefiles)  # Ahora sí debería reconocer el botón

    def browsefiles(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 'C:/')
        print(fname)  # Para depuración, imprime el nombre del archivo
        self.plotsgy(fname)

    def plotsgy(self,file):

        f = segyio.open(file)
        self.layout.addWidget(self.canvas, stretch=1)
        self.canvas.ax.clear()
        x = [0, 1, 2, 3, 4, 5]
        y = [0, 1, 4, 9, 16, 25]
        self.canvas.ax.imshow(x, y, marker='o', linestyle='-', color='b', label="y=x²")
        self.canvas.ax.legend()
        self.canvas.ax.set_title("Example Plot")
        self.canvas.draw()

app = QApplication(sys.argv)
mainwindow = MainWindow()
mainwindow.show()
sys.exit(app.exec_())
