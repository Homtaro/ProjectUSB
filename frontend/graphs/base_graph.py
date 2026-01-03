from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt


class TimeSeriesGraph(QWidget):
    def __init__(self, title="", unit="", parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.data = []

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(10, 20, -10, -10)

        p.setPen(QColor("#666"))
        p.drawRect(rect)

        p.setPen(QColor("#aaa"))
        p.drawText(12, 14, f"{self.title} ({self.unit})")

        if not self.data:
            return

        xs = [x for x, _ in self.data]
        ys = [y for _, y in self.data]

        max_x = max(xs)
        max_y = max(ys) or 1

        pen = QPen(QColor("#3a8"), 2)
        p.setPen(pen)

        prev = None
        for x, y in self.data:
            px = rect.left() + (x / max_x) * rect.width()
            py = rect.bottom() - (y / max_y) * rect.height()

            if prev:
                p.drawLine(prev[0], prev[1], px, py)
            prev = (px, py)
