from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication


class ViewControl:
    def __init__(self, canvas, zoom_limits=(0.3, 5.0)):
        self.canvas = canvas
        self.ax = canvas.ax
        self.zoom_limits = zoom_limits

        self.original_xlim = None
        self.original_ylim = None
        self.last_xlim = None
        self.last_ylim = None

        self._is_panning = False
        self._pan_start = None

        self.canvas.mpl_connect("scroll_event", self._on_scroll)
        self.canvas.mpl_connect("button_press_event", self._on_press)
        self.canvas.mpl_connect("button_release_event", self._on_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)

    def store_original_view(self):
        if self.original_xlim is None or self.original_ylim is None:
            self.original_xlim = self.ax.get_xlim()
            self.original_ylim = self.ax.get_ylim()

    def capture_view(self):
        self.last_xlim = self.ax.get_xlim()
        self.last_ylim = self.ax.get_ylim()

    def restore_view(self):
        if self.last_xlim and self.last_ylim:
            self.ax.set_xlim(self.last_xlim)
            self.ax.set_ylim(self.last_ylim)
            self.canvas.draw()

    def reset_view(self):
        if self.original_xlim and self.original_ylim:
            self.ax.set_xlim(self.original_xlim)
            self.ax.set_ylim(self.original_ylim)
            self.capture_view()
            self.canvas.draw()

    def zoom(self, factor, center=None):
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        if center:
            x_center, y_center = center
        else:
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2

        y_inverted = ylim[1] < ylim[0]

        x_range = (xlim[1] - xlim[0]) * factor / 2
        y_range = abs(ylim[1] - ylim[0]) * factor / 2

        new_xlim = [x_center - x_range, x_center + x_range]

        if y_inverted:
            new_ylim = [y_center + y_range, y_center - y_range]
        else:
            new_ylim = [y_center - y_range, y_center + y_range]

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.capture_view()
        self.canvas.draw()

    def _on_scroll(self, event):
        base_scale = 1.2
        xdata, ydata = event.xdata, event.ydata
        if xdata is None or ydata is None:
            return

        scale_factor = 1 / base_scale if event.button == 'up' else base_scale

        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        new_xlim = [
            xdata - (xdata - cur_xlim[0]) * scale_factor,
            xdata + (cur_xlim[1] - xdata) * scale_factor
        ]
        new_ylim = [
            ydata - (ydata - cur_ylim[0]) * scale_factor,
            ydata + (cur_ylim[1] - ydata) * scale_factor
        ]

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.capture_view()
        self.canvas.draw()

    def _on_press(self, event):
        if event.dblclick and event.button == 1:
            self.reset_view()
            return

        if event.button == 1 and event.xdata is not None and event.ydata is not None:
            self._is_panning = True
            self._pan_start = (event.xdata, event.ydata)
            self.canvas.setCursor(Qt.ClosedHandCursor)

    def _on_release(self, event):
        if event.button == 1:
            self._is_panning = False
            self._pan_start = None
            self.canvas.unsetCursor()

    def _on_motion(self, event):
        if not self._is_panning or event.xdata is None or event.ydata is None:
            return

        dx = self._pan_start[0] - event.xdata
        dy = self._pan_start[1] - event.ydata

        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        self.ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
        self.ax.set_ylim(ylim[0] + dy, ylim[1] + dy)

        self.capture_view()
        self.canvas.draw()
