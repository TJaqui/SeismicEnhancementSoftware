import os
import sys
import segyio
import utils
from PyQt5 import QtWidgets
from PyQt5.uic import loadUi
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)  # Single subplot
        super().__init__(fig)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('seismicaplication.ui', self)  # Pasamos self para enlazar los elementos de la UI
        self.data = None
        self.dataEnhanced = None
        self.canvas = MplCanvas(self)
        #self.canvas1 = MplCanvas(self)

        # Add canvas to a layout inside the main window
        self.layout = QVBoxLayout(self.centralwidget)  
        #self.layout.addWidget(self.canvas)
        self.canvas.setFixedSize(500, 300)
        self.openfile.clicked.connect(self.browsefiles)  
        self.enhancedata.clicked.connect(self.enhanceData)

    def browsefiles(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 'C:/')
        print(fname)  # Para depuración, imprime el nombre del archivo
        self.plotsgy(fname)

    def plotsgy(self,file):
        file = segyio.open(file,ignore_geometry=True)
        self.data = file.trace.raw[:].T
        self.layout.addWidget(self.canvas, stretch=1)
        self.canvas.ax.clear()
        x = [0, 1, 2, 3, 4, 5]
        y = [0, 1, 4, 9, 16, 25]
        self.canvas.ax.imshow(self.data, cmap="gray")
        #self.canvas.ax.legend()
        self.canvas.draw()
    
    def enhanceData(self):
        self.layout.addWidget(self.canvas, stretch=1)
        self.canvas.ax.clear()
        self.dataEnhanced = self.data
        TestData, top, bot, lf, rt = utils.padding(self.dataEnhanced)
        TestData -=TestData.min()
        TestData /=TestData.max()
        
        patches = utils.patchDivision(TestData)
        self.dataEnhanced = utils.seismicEnhancement(patches,TestData.shape)
        self.dataEnhanced = self.dataEnhanced[top:self.dataEnhanced.shape[0]-bot,lf:self.dataEnhanced.shape[1]-rt]
        self.canvas.ax.imshow(self.dataEnhanced, cmap="gray")
        #self.canvas.ax.legend()
        self.canvas.draw()

app = QApplication(sys.argv)
mainwindow = MainWindow()
mainwindow.show()
sys.exit(app.exec_())
