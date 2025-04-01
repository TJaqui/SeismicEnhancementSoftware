import os
import sys
import segyio
import utils
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.uic import loadUi
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)  
        super().__init__(fig)
        self.zoom_factor = 1.2  # Factor for zooming in/out
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def wheelEvent(self, event):
        """Handles mouse scroll for zooming."""
        zoom_in = event.angleDelta().y() > 0  # Detect scroll direction
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        x_range = (xlim[1] - xlim[0]) / (self.zoom_factor if zoom_in else 1/self.zoom_factor)
        y_range = (ylim[1] - ylim[0]) / (self.zoom_factor if zoom_in else 1/self.zoom_factor)

        self.ax.set_xlim([x_center - x_range / 2, x_center + x_range / 2])
        self.ax.set_ylim([y_center - y_range / 2, y_center + y_range / 2])
        self.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('seismicaplication.ui', self)  
        self.data = None
        self.dataEnhanced = None
        self.canvas = MplCanvas(self)
       

        # Add canvas to a layout inside the main window
        self.layout = QVBoxLayout(self.centralwidget)  
      
        self.canvas.setFixedSize(900, 500)
        self.openfile.clicked.connect(self.browsefiles)  
        self.enhancedata.clicked.connect(self.enhanceData)
        #self.savedata.clicked.connect(self.saveData)

    def browsefiles(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 'C:/')
        print(fname)  
        self.plotsgy(fname)

    def plotsgy(self,file):
        file = segyio.open(file,ignore_geometry=True)
        self.data = file.trace.raw[:].T
        self.layout.addWidget(self.canvas, stretch=1,alignment=Qt.AlignRight)
        self.canvas.ax.clear()
        self.canvas.ax.imshow(self.data, cmap="gray")
        self.canvas.draw()
    
    def enhanceData(self):
        try:
            
            self.dataEnhanced = self.data
            TestData, top, bot, lf, rt = utils.padding(self.dataEnhanced)
            TestData -=TestData.min()
            TestData /=TestData.max()
            
            patches = utils.patchDivision(TestData)
            self.layout.addWidget(self.canvas, stretch=1, alignment=Qt.AlignRight)
            self.canvas.ax.clear()
            self.dataEnhanced = utils.seismicEnhancement(patches,TestData.shape)
            self.dataEnhanced = self.dataEnhanced[top:self.dataEnhanced.shape[0]-bot,lf:self.dataEnhanced.shape[1]-rt]
            self.canvas.ax.imshow(self.dataEnhanced, cmap="gray")
            #self.canvas.ax.legend()
            self.canvas.draw()

        except:
            print("First you need to open a file")
   
        
    def saveData(self):
        utils.save2dData(self.dataEnhanced)




app = QApplication(sys.argv)
mainwindow = MainWindow()
mainwindow.show()
sys.exit(app.exec_())
