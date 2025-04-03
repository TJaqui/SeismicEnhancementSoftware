import os
import sys
import segyio
import utils
import time
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.uic import loadUi
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QVBoxLayout, QGraphicsDropShadowEffect, QFrame
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

from PyQt5.QtWidgets import QSizePolicy  # Import QSizePolicy

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('seismicaplication.ui', self)  
        self.data = None
        self.dataEnhanced = None
        self.canvas = MplCanvas(self)
        
        self.topBar.setVisible(True)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.topBar.setGraphicsEffect(shadow)
        
        self.leftBar.setVisible(False)

        # Remove fixed size so it resizes dynamically
        # self.canvas.setFixedSize(900, 500)

        # Set policy to make the canvas expand
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create a layout for the plot area
        self.layout = QVBoxLayout(self.centralwidget) 
        self.layout.setContentsMargins(0, 0, 0, 0) 
          # Make it take full available space

        self.leftBar = self.findChild(QFrame, "leftBar")

        # Create shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setXOffset(5)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.leftBar.setGraphicsEffect(shadow)

        self.progressBar.setVisible(False)
        self.openfile.clicked.connect(self.browsefiles)  
        self.enhancedata.clicked.connect(self.enhanceData)
        self.beforeenhancement.setVisible(False)
        self.afterenhancement.setVisible(False)
        
        self.beforeenhancement.clicked.connect(self.showBeforeEnhancement)  
        self.afterenhancement.clicked.connect(self.showAfterEnhancement)

        # Add file actions
        self.actionOpen_file.triggered.connect(self.browsefiles)

    def browsefiles(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 'C:/')
        print(fname)  
        self.plotsgy(fname)
        self.leftBar.setVisible(True)
        self.beforeenhancement.setVisible(True)
        
        self.afterenhancement.setVisible(False)
        

    def plotsgy(self,file):
        file = segyio.open(file,ignore_geometry=True)
        self.data = file.trace.raw[:].T
        self.layout.addWidget(self.canvas, stretch=1)
        self.layout.setContentsMargins(0, 30, 0, 0)
        self.canvas.lower() 
        self.canvas.ax.clear()
        self.canvas.ax.imshow(self.data, cmap="gray")
        self.canvas.draw()
    
    def enhanceData(self):
        try:
            
            self.dataEnhanced = self.data
            TestData, top, bot, lf, rt = utils.padding(self.dataEnhanced)
      
            TestData -= TestData.min()
            TestData /= TestData.max()
 
            patches = utils.patchDivision(TestData)
            self.progressBar.setValue(40)
            self.layout.addWidget(self.canvas, stretch=1)
            self.canvas.ax.clear()
            self.dataEnhanced = utils.seismicEnhancement(patches,TestData.shape)
            self.progressBar.setValue(90)
            self.dataEnhanced = self.dataEnhanced[top:self.dataEnhanced.shape[0]-bot,lf:self.dataEnhanced.shape[1]-rt]
            self.canvas.ax.imshow(self.dataEnhanced, cmap="gray")
            #self.canvas.ax.legend()
            self.canvas.draw()
            self.afterenhancement.setVisible(True)
    
          
        except:
            print("First you need to open a file")
   
    def showBeforeEnhancement(self):
        """Displays the original seismic data before enhancement."""
        if self.data is not None:
            self.canvas.ax.clear()
            self.canvas.ax.imshow(self.data, cmap="gray")
            self.canvas.draw()

    def showAfterEnhancement(self):
        """Displays the enhanced seismic data."""
        if self.dataEnhanced is not None:
            self.canvas.ax.clear()
            self.canvas.ax.imshow(self.dataEnhanced, cmap="gray")
            self.canvas.draw() 

    def saveData(self):
        utils.save2dData(self.dataEnhanced)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
