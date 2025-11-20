# Permite que el usuario seleccione el ROI con el mouse.
# Esto es lo que describe Beyeler cuando habla de “manual ROI selection”

import cv2

class RegionSelector:
    def __init__(self):
        self.dragging = False
        self.ix = self.iy = 0
        self.fx = self.fy = 0
        self.roi_ready = False

    def reset(self):
        self.roi_ready = False

    def select_roi(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.dragging = True
            self.ix, self.iy = x, y

        elif event == cv2.EVENT_MOUSEMOVE and self.dragging:
            self.fx, self.fy = x, y

        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = False
            self.fx, self.fy = x, y
            self.roi_ready = True

    def get_roi(self):
        x1, y1 = min(self.ix, self.fx), min(self.iy, self.fy)
        x2, y2 = max(self.ix, self.fx), max(self.iy, self.fy)
        return (x1, y1, x2 - x1, y2 - y1)
