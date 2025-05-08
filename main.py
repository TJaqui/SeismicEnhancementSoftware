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
from finetuning import parallelTrain
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy 
from PyQt5.QtWidgets import QButtonGroup
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QVBoxLayout, QGraphicsDropShadowEffect, QCheckBox, QFrame, QProgressBar, QMessageBox, QLineEdit, QPushButton, QHBoxLayout, QLabel, QDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

global fname, x_start, x_end, y_start, y_end, datamin, datamax
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


class RangeDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Set Ranges")
        self.setFixedSize(400, 400)

        self.data = data.copy()
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
from matplotlib.widgets import RectangleSelector

class RangeDialogAd(QDialog):
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
        self.batch = QLineEdit("5")
        self.iterations = QLineEdit("1")
        self.epochs = QLineEdit("30")
        self.gensamples = QLineEdit("100")

        layout = QVBoxLayout()

        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("x from"))
        x_layout.addWidget(self.x_from)
        x_layout.addWidget(QLabel("-"))
        x_layout.addWidget(self.x_to)
        layout.addLayout(x_layout)

        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("y from"))
        y_layout.addWidget(self.y_from)
        y_layout.addWidget(QLabel("-"))
        y_layout.addWidget(self.y_to)
        layout.addLayout(y_layout)

        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Batch"))
        z_layout.addWidget(self.batch)
        z_layout.addWidget(QLabel("Iterations"))
        z_layout.addWidget(self.iterations)
        layout.addLayout(z_layout)

        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Epochs"))
        a_layout.addWidget(self.epochs)
        a_layout.addWidget(QLabel("Samples"))
        a_layout.addWidget(self.gensamples)
        layout.addLayout(a_layout)

        layout.addWidget(self.canvas)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("ok")
        cancel_btn = QPushButton("cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        if self.data is not None:
            self.canvas.ax.imshow(self.data, cmap="gray")
            self.selector = RectangleSelector(
                self.canvas.ax,
                self.on_select,
                useblit=True,
                button=[1],  # Left click
                minspanx=5,
                minspany=5,
                spancoords='pixels',
                interactive=True
            )
            self.canvas.draw()

    def on_select(self, eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)

        # Ordenar coordenadas
        x_start, x_end = sorted((x1, x2))
        y_start, y_end = sorted((y1, y2))

        self.x_from.setText(str(x_start))
        self.x_to.setText(str(x_end))
        self.y_from.setText(str(y_start))
        self.y_to.setText(str(y_end))

        self.update_plot()

    def get_ranges(self):
        return (int(self.x_from.text()), int(self.x_to.text()),
                int(self.y_from.text()), int(self.y_to.text()))
    def get_train_data(self):
        return (int(self.batch.text()), int(self.iterations.text()),
                int(self.epochs.text()), int(self.gensamples.text()))

    def update_plot(self):
        try:
            x_start, x_end, y_start, y_end = self.get_ranges()
            if self.data is not None:
                cropped = self.data[y_start:y_end, x_start:x_end]
                self.canvas.ax.clear()
                self.canvas.ax.imshow(cropped, cmap="gray")
                self.canvas.draw()
        except Exception:
            pass

class DialogDim(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select data dimensions")
        self.setFixedSize(200, 200)

    
        self.d3 = QCheckBox("3D")
        self.d2 = QCheckBox("2D")

        # Conectar para comportamiento exclusivo
        self.d3.stateChanged.connect(self.on_d3_checked)
        self.d2.stateChanged.connect(self.on_d2_checked)

        layout = QVBoxLayout()
        x_layout = QHBoxLayout()
        x_layout.addWidget(self.d3)
        x_layout.addWidget(self.d2)
        layout.addLayout(x_layout)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("ok")
        cancel_btn = QPushButton("cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def on_d3_checked(self, state):
        if state:
            self.d2.setChecked(False)

    def on_d2_checked(self, state):
        if state:
            self.d3.setChecked(False)

    def get_Checked(self):
        if self.d3.isChecked():
            return True, False
        if self.d2.isChecked():
            return False, True

    

   
    
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

        #setenable checkboxes
        self.Seismic.setEnabled(False)
        self.Gray.setEnabled(False) 
        self.Wiggle.setEnabled(False)
        self.enhancedata.setEnabled(False) 
        self.adapttodata.setEnabled(False) 
        self.savefile.setEnabled(False) 
        self.openfile.clicked.connect(self.browsefiles) 
        
        self.enhancedata.clicked.connect(self.enhanceData)
        
        self.beforeenhancement.setVisible(False)
        self.afterenhancement.setVisible(False)
        
        self.beforeenhancement.clicked.connect(self.showBeforeEnhancement)  
        self.adapttodata.clicked.connect(self.AdaptToData)  
        self.afterenhancement.clicked.connect(self.showAfterEnhancement) 
        self.savefile.clicked.connect(self.saveData) 
        self.labeldata.setStyleSheet("font-weight: bold;")
        self.ColorButtons()

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

            file = segyio.open(file,ignore_geometry=True)
            self.data = file.trace.raw[:].T
            
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

            file = segyio.open(file)
            self.data = file.iline[100].T
            
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

    def saveData(self):
        dname = QFileDialog.getExistingDirectory(self, 'Open file', 'C:/')
        utils.save2dData(self.dataEnhanced,fname, dname, datamin, datamax)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
