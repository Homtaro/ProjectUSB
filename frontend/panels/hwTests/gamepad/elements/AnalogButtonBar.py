from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics
from PySide6.QtCore import Qt, QRectF


class AnalogButtonBar(QWidget):
    """
    Displays a gamepad button as an analog bar (0.0 - 1.0).
    Digital buttons should simply set value to 1.0 when pressed.
    """

    def __init__(
        self,
        label: str,
        parent=None,
        height: int = 18,
        show_value: bool = False,
    ):
        super().__init__(parent)

        self.label = label
        self.value = 0.0
        self.show_value = show_value

        self.font = QFont("Segoe UI", 9)
        fm = QFontMetrics(self.font)

        #self.label_width = fm.horizontalAdvance(label) + 12

        self.label_width = 80
        self.setFixedHeight(height)
        self.setMinimumWidth(220)

        self._bg_color = QColor("#1e1e1e")
        self._fill_color = QColor("#3aa675")
        self._border_color = QColor("#333")
        self._text_color = QColor("#e0e0e0")

    # ================= API =================

    def set_value(self, v: float):
        v = max(0.0, min(1.0, v))
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

        rect = self.rect()
        margin = 6

        painter.setFont(self.font)

        # ---- Label ----
        painter.setPen(self._text_color)
        painter.drawText(
            QRectF(0, 0, self.label_width, rect.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            self.label
        )

        # ---- Bar geometry ----
        bar_x = self.label_width + margin
        bar_width = rect.width() - bar_x - margin
        bar_height = rect.height() - 6
        bar_y = (rect.height() - bar_height) / 2

        bar_rect = QRectF(bar_x, bar_y, bar_width, bar_height)

        # ---- Background ----
        painter.setPen(self._border_color)
        painter.setBrush(self._bg_color)
        painter.drawRoundedRect(bar_rect, 4, 4)

        # ---- Fill ----
        if self.value > 0:
            fill_width = bar_width * self.value
            fill_rect = QRectF(bar_x, bar_y, fill_width, bar_height)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._fill_color)
            painter.drawRect(fill_rect)

        # ---- Optional value ----
        if self.show_value:
            painter.setPen(QColor("#bbbbbb"))
            painter.setFont(QFont("Consolas", 8))
            painter.drawText(bar_rect, Qt.AlignCenter, f"{self.value:.2f}")
