from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)  # Solo un eje principal

        super().__init__(self.fig)
        self.colorbar = None
        self.setParent(parent)

        self.zoom_factor = 1.2
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def wheelEvent(self, event):
        """Handles mouse scroll for zooming."""
        zoom_in = event.angleDelta().y() > 0  # Detect scroll direction
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        x_range = (xlim[1] - xlim[0]) / (self.zoom_factor if zoom_in else 1 / self.zoom_factor)
        y_range = (ylim[1] - ylim[0]) / (self.zoom_factor if zoom_in else 1 / self.zoom_factor)

        self.ax.set_xlim([x_center - x_range / 2, x_center + x_range / 2])
        self.ax.set_ylim([y_center - y_range / 2, y_center + y_range / 2])
        self.draw()
