from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt


class AxisBar(QWidget):
    """
    Visualizes a single analog axis in range [-1.0, 1.0].
    """

    def __init__(
        self,
        label: str = "",
        parent=None,
        width: int = 160,
        height: int = 18,
        show_value: bool = True,
    ):
        super().__init__(parent)

        self.label = label
        self.show_value = show_value
        self.value = 0.0

        self.setFixedSize(width, height + (16 if label else 0))

        # Colors
        self._bg = QColor("#1e1e1e")
        self._border = QColor("#3a3a3a")
        self._center = QColor("#666")
        self._fill_pos = QColor("#3aa675")
        self._fill_neg = QColor("#a35a5a")
        self._text = QColor("#e0e0e0")

    # ================= API =================

    def set_value(self, v: float):
        """
        Set axis value (-1.0 .. +1.0).
        """
        v = max(-1.0, min(1.0, v))
        if abs(self.value - v) > 0.001:
            self.value = v
            self.update()

    def reset(self):
        self.value = 0.0
        self.update()

    # ================= DRAW =================

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        label_offset = 16 if self.label else 0
        bar_h = h - label_offset

        # ---- Label ----
        if self.label:
            painter.setPen(self._text)
            painter.drawText(0, 0, w, 14, Qt.AlignCenter, self.label)

        bar_y = label_offset
        center_x = w // 2

        # ---- Background ----
        painter.setPen(QPen(self._border, 1))
        painter.setBrush(self._bg)
        painter.drawRoundedRect(0, bar_y, w, bar_h, 4, 4)

        # ---- Center line ----
        painter.setPen(QPen(self._center, 1))
        painter.drawLine(center_x, bar_y, center_x, bar_y + bar_h)

        # ---- Fill ----
        half = w // 2
        fill = int(abs(self.value) * half)

        if self.value > 0:
            painter.setBrush(self._fill_pos)
            painter.setPen(Qt.NoPen)
            painter.drawRect(center_x, bar_y, fill, bar_h)
        elif self.value < 0:
            painter.setBrush(self._fill_neg)
            painter.setPen(Qt.NoPen)
            painter.drawRect(center_x - fill, bar_y, fill, bar_h)

        # ---- Value text ----
        if self.show_value:
            painter.setPen(self._text)
            painter.drawText(
                0,
                bar_y,
                w,
                bar_h,
                Qt.AlignCenter,
                f"{self.value:+.2f}"
            )
