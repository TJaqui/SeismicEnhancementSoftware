import os
import sys
import segyio
import utils
import time
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets
from PyQt5.uic import loadUi
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QVBoxLayout, QGraphicsDropShadowEffect, QFrame, QProgressBar, QMessageBox, QLineEdit, QPushButton, QHBoxLayout, QLabel, QDialog
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
class RangeDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Set Ranges")
        self.setFixedSize(400, 400)

        self.data = data
        self.canvas = MplCanvas(self)

        self.x_from = QLineEdit("0")
        self.x_to = QLineEdit(str(data.shape[1]) if data is not None else "500")
        self.y_from = QLineEdit("0")
        self.y_to = QLineEdit(str(data.shape[0]) if data is not None else "500")

        layout = QVBoxLayout()

        # X Range
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("x from"))
        x_layout.addWidget(self.x_from)
        x_layout.addWidget(QLabel("-"))
        x_layout.addWidget(self.x_to)
        layout.addLayout(x_layout)

        # Y Range
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("y from"))
        y_layout.addWidget(self.y_from)
        y_layout.addWidget(QLabel("-"))
        y_layout.addWidget(self.y_to)
        layout.addLayout(y_layout)

        # Canvas for plot
        layout.addWidget(self.canvas)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("ok")
        cancel_btn = QPushButton("cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # Update preview when values change
        for box in [self.x_from, self.x_to, self.y_from, self.y_to]:
            box.textChanged.connect(self.update_plot)

        self.setLayout(layout)
        self.update_plot()  # Initial preview

    def get_ranges(self):
        return (int(self.x_from.text()), int(self.x_to.text()),
                int(self.y_from.text()), int(self.y_to.text()))

    def update_plot(self):
        try:
            x_start, x_end, y_start, y_end = self.get_ranges()
            if self.data is not None:
                cropped = self.data[y_start:y_end, x_start:x_end]
                self.canvas.ax.clear()
                self.canvas.ax.imshow(cropped, cmap="gray")
                self.canvas.draw()
        except Exception as e:
            # Ignore invalid input temporarily
            pass
    
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('seismicaplication.ui', self)  
        self.data = None
        self.dataEnhanced = None
        self.canvas = MplCanvas(self)
        self.progressbar = QProgressBar()
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(100)
        
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

        self.enhancedata.setEnabled(False) 
        self.adapttodata.setEnabled(False) 
        self.savefile.setEnabled(False) 
        self.openfile.clicked.connect(self.browsefiles) 
        
        self.enhancedata.clicked.connect(self.enhanceData)
        
        self.beforeenhancement.setVisible(False)
        self.afterenhancement.setVisible(False)
        
        self.beforeenhancement.clicked.connect(self.showBeforeEnhancement)  
        self.adapttodata.clicked.connect(self.showRangeDialog)  
        self.afterenhancement.clicked.connect(self.showAfterEnhancement) 
        
        self.labeldata.setStyleSheet("font-weight: bold;")

    def browsefiles(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 'C:/')
        print(fname)
        try:  
            self.plotsgy(fname)
            self.leftBar.setVisible(True)
            self.beforeenhancement.setVisible(True)
            self.enhancedata.setEnabled(True)
            self.adapttodata.setEnabled(True) 
            self.savefile.setEnabled(True)  
            self.afterenhancement.setVisible(False)
            
        except:
            pass

    def plotsgy(self,file):
        
            file = segyio.open(file,ignore_geometry=True)
            self.data = file.trace.raw[:].T
            self.layout.addWidget(self.canvas, stretch=1)
            self.layout.setContentsMargins(0, 30, 0, 0)
            self.canvas.lower() 
            self.canvas.ax.clear()
            self.canvas.ax.imshow(self.data, cmap="gray")
            self.canvas.draw()
        
    def showRangeDialog(self):
        dialog = RangeDialog(self, data=self.data)
        if dialog.exec_() == QDialog.Accepted:
            x_start, x_end, y_start, y_end = dialog.get_ranges()
            print(f"Selected range: x={x_start}-{x_end}, y={y_start}-{y_end}")
            if self.data is not None:
                cropped = self.data[y_start:y_end, x_start:x_end]
                self.canvas.ax.clear()
                self.canvas.ax.imshow(cropped, cmap="gray")
                self.canvas.draw()
                
    def enhanceData(self):
        try:
            
            
            QApplication.processEvents()  # <- Forzar actualización UI
            
            self.dataEnhanced = self.data
            TestData, top, bot, lf, rt = utils.padding(self.dataEnhanced)
            
            QApplication.processEvents()
            self.layout.addWidget(self.progressbar)
            self.progressbar.setValue(0)
            TestData -= TestData.min()
            TestData /= TestData.max()
            self.progressbar.setValue(10)
            time.sleep(0.01)
            QApplication.processEvents()
            self.progressbar.setValue(20)
            patches = utils.patchDivision(TestData)
            self.progressbar.setValue(40)
            QApplication.processEvents()
            time.sleep(0.01)
            self.progressbar.setValue(60)
            
            self.layout.addWidget(self.canvas, stretch=1)
            self.canvas.ax.clear()
            time.sleep(0.01)
            
            self.dataEnhanced = utils.seismicEnhancement(patches, TestData.shape)
            self.progressbar.setValue(70)
            time.sleep(0.01)
            self.progressbar.setValue(80)
            time.sleep(0.01)
            self.progressbar.setValue(90)
            self.layout.removeWidget(self.progressbar)
            self.progressbar.deleteLater()
            QApplication.processEvents()
            time.sleep(0.3)
            
            
            self.dataEnhanced = self.dataEnhanced[top:self.dataEnhanced.shape[0]-bot, lf:self.dataEnhanced.shape[1]-rt]
            self.canvas.ax.imshow(self.dataEnhanced, cmap="gray")
            self.canvas.draw()
            
            self.afterenhancement.setVisible(True)
            
            QApplication.processEvents()
            
        except Exception as e:
            error_dialog = QMessageBox(self)
            error_dialog.setWindowTitle("Enhancement Error")
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText("An error occurred during data enhancement.")
            error_dialog.setInformativeText(str(e))
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec_()
   
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
