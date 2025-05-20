import os
import sys
import segyio
import utils
import time
from PyQt5.QtGui import QColor

from PyQt5.uic import loadUi
from finetuning import parallelTrain
from PyQt5.QtWidgets import QSizePolicy 
from PyQt5.QtWidgets import QButtonGroup
from PyQt5.QtWidgets import QMainWindow, QAction, QGraphicsDropShadowEffect, QProgressBar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from dialog import *

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

global fname, x_start, x_end, y_start, y_end, datamin, datamax

   
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('seismicaplication.ui', self)  
        self.data = None
        self.dataEnhanced = None
        self.datatoEnhanced = None
        self.d3 = False
        self.d2 = True
        self.canvas = MplCanvas(self)
        self.progressbar = QProgressBar()
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(100)
        self.file = None
        self.ilines = None
        self.xlines = None
        self.setWindowIcon(QIcon("icons/logo.png"))

        self.topBar.setVisible(True)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.topBar.setGraphicsEffect(shadow)
        
        self.leftBar.setVisible(False)



        menubar = self.menuBar()
        about_menu = menubar.addMenu("About")

        # Create About action
        self.actionAbout = QAction("About", self)
        self.actionAbout.triggered.connect(self.about)
        about_menu.addAction(self.actionAbout)
        help_menu = menubar.addMenu("Help")

        # Create About action
        self.actionHelp = QAction("Help", self)
        self.actionHelp.triggered.connect(self.help)
        help_menu.addAction(self.actionHelp)

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

        #setenable checkboxes
        self.Seismic.setEnabled(False)
        self.Gray.setEnabled(False) 
        self.Wiggle.setEnabled(False)
        self.enhancedata.setEnabled(False) 
        self.adapttodata.setEnabled(False) 
        self.savefile.setEnabled(False) 
        self.openfile.clicked.connect(self.browsefiles) 
        
        self.beforeenhancement.setVisible(False)
        self.afterenhancement.setVisible(False)
        
        self.Seismic_2.setVisible(False)
        self.Gray_2.setVisible(False) 
        self.Wiggle_2.setVisible(False)
        self.enhancedata_2.setVisible(False) 
        self.adapttodata_2.setVisible(False) 
        self.ilineN.setVisible(False) 
        self.clineN.setVisible(False) 
        self.iline.setVisible(False) 
        self.crossline.setVisible(False)       

        self.enhancedata.clicked.connect(self.enhanceData)
        self.enhancedata_2.clicked.connect(self.enhanceData2)
        self.beforeenhancement.clicked.connect(self.showBeforeEnhancement)  
        self.adapttodata.clicked.connect(self.AdaptToData)  
        self.adapttodata_2.clicked.connect(self.AdaptToData)  
        self.afterenhancement.clicked.connect(self.showAfterEnhancement) 
        self.savefile.clicked.connect(self.saveData) 
        self.ilineN.valueChanged.connect(self.update_plot)
        self.clineN.valueChanged.connect(self.update_plot)
        self.labeldata.setStyleSheet("font-weight: bold;")
        self.ColorButtons()
        self.Sectionic()

    def ColorButtons(self):
        self.colorGroup = QButtonGroup(self)
        self.colorGroup.setExclusive(True)

        self.colorGroup.addButton(self.Seismic, 0)  # Seismic
        self.colorGroup.addButton(self.Gray, 1)  # Gray
        self.colorGroup.addButton(self.Wiggle, 2)  # Wiggle
        
        self.colorGroup.buttonClicked[int].connect(self.ColorSelected)

    def ColorSelected(self, id):
        colors = ["seismic", "gray", "wiggle"]
        self.Color = colors[id]
        print("Color seleccionado:", self.Color)
        self.canvas.ax.clear()
        if self.afterenhancement.isVisible() and self.dataEnhanced is not None:
            self.canvas.ax.imshow(self.dataEnhanced, cmap=self.Color)
        elif self.data is not None:
            self.canvas.ax.imshow(self.data, cmap=self.Color)
        self.canvas.draw()

    def Sectionic(self):
        self.icGroup = QButtonGroup(self)
        self.icGroup.setExclusive(True)

        self.icGroup.addButton(self.iline, 0)  # Seismic
        self.icGroup.addButton(self.crossline, 1)  # Gray

        self.icGroup.buttonClicked[int].connect(self.icSelected)


    def icSelected(self, id):
        ics = ["iline", "crossline"]
        self.ic = ics[id]
        print("ic seleccionado:", self.ic)


    def browsefiles(self):
        
        global fname
        
        #print(fname)
        try:
            dimen = DialogDim(self)
            if dimen.exec_() == QDialog.Accepted:    
                fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 'C:/')
                d3, d2 = dimen.get_Checked()
                self.d2 = d2
                self.d3 = d3
            if d2:
                self.plotsgy2d(fname)
            elif d3:
                self.Seismic.setVisible(False)
                self.Gray.setVisible(False) 
                self.Wiggle.setVisible(False)
                self.enhancedata.setVisible(False) 
                self.adapttodata.setVisible(False) 

                
                self.Seismic_2.setVisible(True)
                self.Gray_2.setVisible(True) 
                self.Wiggle_2.setVisible(True)
                self.enhancedata_2.setVisible(True) 
                self.adapttodata_2.setVisible(True)  
                self.ilineN.setVisible(True) 
                self.clineN.setVisible(True) 
                self.iline.setVisible(True) 
                self.crossline.setVisible(True)   
                self.plotsgy3d(fname)    

            self.leftBar.setVisible(True)
            self.beforeenhancement.setVisible(True)
            self.enhancedata.setEnabled(True)
            self.adapttodata.setEnabled(True) 
            self.savefile.setEnabled(True)  
            self.afterenhancement.setVisible(False)
            self.Seismic.setEnabled(True)
            self.Gray.setEnabled(True)
            self.Wiggle.setEnabled(True)
            
        except:
            pass

    def plotsgy2d(self,file):
            
            global datamin, datamax

            self.file = segyio.open(file,ignore_geometry=True)
            self.data = self.file.trace.raw[:].T
            
            datamin =  self.data.min()
            datamax = self.data.max()
            
            self.data -= self.data.min()
            self.data /= self.data.max()

            self.layout.addWidget(self.canvas, stretch=1)
            self.layout.setContentsMargins(0, 30, 0, 0)
            self.canvas.lower() 
            self.canvas.ax.clear()
            self.colorGroup.button(1).setChecked(True)
            self.ColorSelected(1)
            cmap = getattr(self, "Color", "gray")
            self.canvas.ax.imshow(self.data, cmap=cmap)
            self.canvas.draw()
        
    def plotsgy3d(self,file):
            
            global datamin, datamax

            self.file = segyio.open(file)
            self.ilines = list(self.file.ilines)
            self.xlines = list(self.file.xlines)

            self.ilineN.setMinimum(self.ilines[0])
            self.ilineN.setMaximum(self.ilines[-1])

            self.clineN.setMinimum(self.xlines[0])
            self.clineN.setMaximum(self.xlines[-1])
            self.data = self.file.iline[self.ilines[0]].T
            
            self.iline.setChecked(True)
            datamin =  self.data.min()
            datamax = self.data.max()
            
            self.data -= self.data.min()
            self.data /= self.data.max()

            self.layout.addWidget(self.canvas, stretch=1)
            self.layout.setContentsMargins(0, 30, 0, 0)
            self.canvas.lower() 
            self.canvas.ax.clear()
            
            self.colorGroup.button(1).setChecked(True)
      
            self.ColorSelected(1)
            cmap = getattr(self, "Color", "gray")
            self.canvas.ax.imshow(self.data, cmap=cmap)
            self.canvas.draw()
            

    def update_plot(self):

        # Get selected line type and number
        if self.iline.isChecked():
            line_num = self.ilineN.value()
            self.data = self.file.iline[line_num].T
        elif self.crossline.isChecked():
            line_num = self.clineN.value()
            self.data = self.file.xline[line_num].T
        else:
            return  # No valid option selected

        # Normalize data
        datamin = self.data.min()
        datamax = self.data.max()
        self.data -= datamin
        if datamax != 0:
            self.data /= datamax

        # Redraw
        self.canvas.ax.clear()
        cmap = getattr(self, "Color", "gray")
        self.canvas.ax.imshow(self.data, cmap=cmap)
        self.canvas.draw()
        print("plot changed")

    def enhanceData(self):
        
        try:
            global x_start, x_end, y_start, y_end
            dialog = RangeDialog(self, data=self.data)
            if dialog.exec_() == QDialog.Accepted:
                x_start, x_end, y_start, y_end = dialog.get_ranges()
            QApplication.processEvents()  # <- Forzar actualización UI
            self.dataEnhanced = self.data.copy()
            self.datatoEnhanced = self.data[y_start: y_end,x_start: x_end ]
            
            TestData, top, bot, lf, rt = utils.padding(self.datatoEnhanced)
     
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
            
            self.datatoEnhanced = utils.seismicEnhancement(patches, TestData.shape)
      
            self.progressbar.setValue(70)
            time.sleep(0.01)
            self.progressbar.setValue(80)
            time.sleep(0.01)
            self.progressbar.setValue(90)
            self.layout.removeWidget(self.progressbar)
            self.progressbar.deleteLater()
            QApplication.processEvents()
            time.sleep(0.3)
 
            self.dataEnhanced[ y_start: y_end, x_start: x_end ] = self.datatoEnhanced[top:self.datatoEnhanced.shape[0]-bot, lf:self.datatoEnhanced.shape[1]-rt]

            cmap = getattr(self, "Color", "gray") 
            self.canvas.ax.imshow(self.dataEnhanced, cmap=cmap)
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
    
    def enhanceData2(self):
        
        try:
            global x_start, x_end, y_start, y_end
            
            dialog = RangeDialogEn3D(self, data=self.data, ilines=self.ilines, xlines=self.xlines)
            if dialog.exec_() == QDialog.Accepted:
                x_start = dialog.get_ranges()

            
            QApplication.processEvents()  # <- Forzar actualización UI
  
            
            self.dataEnhanced = self.data.copy()
            self.datatoEnhanced = self.data[y_start: y_end,x_start: x_end ]
            
            TestData, top, bot, lf, rt = utils.padding(self.datatoEnhanced)

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
            
            self.datatoEnhanced = utils.seismicEnhancement(patches, TestData.shape)
      
            self.progressbar.setValue(70)
            time.sleep(0.01)
            self.progressbar.setValue(80)
            time.sleep(0.01)
            self.progressbar.setValue(90)
            self.layout.removeWidget(self.progressbar)
            self.progressbar.deleteLater()
            QApplication.processEvents()
            time.sleep(0.3)
 
            self.dataEnhanced[ y_start: y_end, x_start: x_end ] = self.datatoEnhanced[top:self.datatoEnhanced.shape[0]-bot, lf:self.datatoEnhanced.shape[1]-rt]

            cmap = getattr(self, "Color", "gray") 
            self.canvas.ax.imshow(self.dataEnhanced, cmap=cmap)
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
            cmap = getattr(self, "Color", "gray") 
            self.canvas.ax.imshow(self.data, cmap=cmap)
            self.canvas.draw()

    def showAfterEnhancement(self):
        """Displays the enhanced seismic data."""
    
        if self.dataEnhanced is not None:
            self.canvas.ax.clear()
            cmap = getattr(self, "Color", "gray")
            self.canvas.ax.imshow(self.dataEnhanced, cmap=cmap)
            self.canvas.draw() 

    def AdaptToData(self):
        try:
            dialog = RangeDialogAd(self, data=self.data)
            if dialog.exec_() == QDialog.Accepted:
                x_start, x_end, y_start, y_end = dialog.get_ranges()
                batch_size, iterations, epochs, gen_samples = dialog.get_ranges()
                #print(f"Selected range: x={x_start}-{x_end}, y={y_start}-{y_end}")
                if self.data is not None:
                    cropped = self.data[y_start:y_end, x_start:x_end]
                    self.canvas.ax.clear()
                    self.canvas.ax.imshow(cropped, cmap="gray")
                    self.canvas.draw()
            
            parallelTrain(self.data[y_start:y_end, x_start: x_end], batch_size, epochs, iterations, gen_samples)
        except Exception as e:
                    error_dialog = QMessageBox(self)
                    error_dialog.setWindowTitle("Enhancement Error")
                    error_dialog.setIcon(QMessageBox.Critical)
                    error_dialog.setText("An error occurred during data enhancement.")
                    error_dialog.setInformativeText(str(e))
                    error_dialog.setStandardButtons(QMessageBox.Ok)
                    error_dialog.exec_()
    
    # Menu bar functions
    def about(self):
        dialog = AboutDialog(self)
        dialog.exec_() 
    def help(self):
        dialog = HelpDialog(self)
        dialog.exec_() 
            

    def saveData(self):
        dname = QFileDialog.getExistingDirectory(self, 'Open file', 'C:/')
        utils.save2dData(self.dataEnhanced,fname, dname, datamin, datamax)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setWindowIcon(QIcon("logo.png"))
    mainwindow = MainWindow()
    mainwindow.setWindowTitle("NED")
    mainwindow.show()
    sys.exit(app.exec_())
