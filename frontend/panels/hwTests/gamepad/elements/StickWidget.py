
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF


class StickWidget(QWidget):
    """
    Visualizes an analog stick as a circular area with a moving dot.
    Input values must be normalized to range [-1.0, 1.0].
    """

    def __init__(
        self,
        label: str = "",
        parent=None,
        size: int = 140,
        deadzone: float = 0.15,
        show_values: bool = True,
    ):
        super().__init__(parent)

        self.label = label
        self.deadzone = deadzone
        self.show_values = show_values

        self.x = 0.0
        self.y = 0.0

        self.setFixedSize(size, size + (18 if label else 0))

        # Colors
        self._bg_color = QColor("#1e1e1e")
        self._border_color = QColor("#3a3a3a")
        self._stick_color = QColor("#3aa675")
        self._deadzone_color = QColor("#444")
        self._axis_color = QColor("#555")
        self._text_color = QColor("#e0e0e0")

    # ================= API =================

    def set_value(self, x: float, y: float):
        """
        Set stick position (normalized -1.0 to 1.0).
        Values are clamped to a unit circle.
        """
        mag = math.hypot(x, y)
        if mag > 1.0:
            x /= mag
            y /= mag

        if abs(self.x - x) > 0.001 or abs(self.y - y) > 0.001:
            self.x = x
            self.y = y
            self.update()

    def reset(self):
        self.x = 0.0
        self.y = 0.0
        self.update()

    # ================= DRAW =================

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        label_offset = 18 if self.label else 0
        radius = min(w, h - label_offset) // 2 - 6
        center = QPointF(w / 2, label_offset + (h - label_offset) / 2)

        # ---- Label ----
        if self.label:
            painter.setPen(self._text_color)
            painter.drawText(0, 0, w, 16, Qt.AlignCenter, self.label)

        # ---- Outer circle ----
        painter.setPen(QPen(self._border_color, 2))
        painter.setBrush(self._bg_color)
        painter.drawEllipse(center, radius, radius)

        # ---- Deadzone ----
        if self.deadzone > 0:
            dz_radius = radius * self.deadzone
            painter.setPen(QPen(self._deadzone_color, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, dz_radius, dz_radius)

        # ---- Axes ----
        painter.setPen(QPen(self._axis_color, 1))
        painter.drawLine(
            center.x() - radius, center.y(),
            center.x() + radius, center.y()
        )
        painter.drawLine(
            center.x(), center.y() - radius,
            center.x(), center.y() + radius
        )

        # ---- Stick dot ----
        dot_x = center.x() + self.x * radius
        dot_y = center.y() - self.y * radius  # invert Y for screen space

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._stick_color)
        painter.drawEllipse(QPointF(dot_x, dot_y), 6, 6)

        # ---- Numeric values ----
        if self.show_values:
            painter.setPen(self._text_color)
            painter.drawText(
                0, h - 16, w, 16,
                Qt.AlignCenter,
                f"X: {self.x:+.2f}  Y: {self.y:+.2f}"
            )
