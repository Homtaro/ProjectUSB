from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF, QRectF
import math


class GamepadVisual(QWidget):
    """
    Visual Xbox-style gamepad representation with heatmap.
    All values are normalized:
        - buttons: 0.0 .. 1.0
        - sticks:  -1.0 .. +1.0
        - triggers: 0.0 .. 1.0
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(420, 280)

        # ================= STATE =================

        self.buttons = {}  # name -> intensity (0..1)
        self.triggers = {  # LT / RT
            "LT": 0.0,
            "RT": 0.0,
        }

        self.sticks = {
            "L": (0.0, 0.0),
            "R": (0.0, 0.0),
        }

        # ================= COLORS =================

        self._body = QColor("#1c1c1c")
        self._outline = QColor("#444")
        self._inactive = QColor("#2a2a2a")
        self._active = QColor("#3aa675")
        self._axis = QColor("#555")

    # ================= API =================

    def set_button(self, name: str, value: float):
        self.buttons[name] = max(0.0, min(1.0, value))
        self.update()

    def set_trigger(self, name: str, value: float):
        if name in self.triggers:
            self.triggers[name] = max(0.0, min(1.0, value))
            self.update()

    def set_stick(self, stick: str, x: float, y: float):
        mag = math.hypot(x, y)
        if mag > 1.0:
            x /= mag
            y /= mag
        self.sticks[stick] = (x, y)
        self.update()

    def reset(self):
        self.buttons.clear()
        self.triggers["LT"] = 0.0
        self.triggers["RT"] = 0.0
        self.sticks["L"] = (0.0, 0.0)
        self.sticks["R"] = (0.0, 0.0)
        self.update()

    # ================= DRAW =================

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # ---- Body ----
        p.setPen(QPen(self._outline, 2))
        p.setBrush(self._body)

        # Body spans roughly from 0.30 to 0.94 vertically
        body_margin_x = w * 0.1
        body_margin_y = h * 0.30

        p.drawRoundedRect(
            body_margin_x,
            body_margin_y,
            w - (body_margin_x * 2),
            h - (body_margin_y * 1.2),
            40, 40
        )

        # ================= SHOULDERS (Fixed positions) =================

        # Bumpers (LB / RB)
        self._draw_bumper(p, QPointF(w * 0.25, h * 0.27), "LB")
        self._draw_bumper(p, QPointF(w * 0.75, h * 0.27), "RB")

        # Triggers (LT / RT)
        self._draw_trigger(p, QPointF(w * 0.25, h * 0.15), "LT")
        self._draw_trigger(p, QPointF(w * 0.75, h * 0.15), "RT")

        # ================= MAIN INPUTS (Symmetrically Aligned) =================
        # Body vertical center is approx ~0.62
        # Top Row Y    = 0.50 (Left Stick, Buttons, Start/Back)
        # Bottom Row Y = 0.74 (Right Stick, D-Pad)

        row_top = h * 0.50
        row_bot = h * 0.74

        # ---- STICKS ----
        self._draw_stick(p, QPointF(w * 0.28, row_top), "L")
        self._draw_stick(p, QPointF(w * 0.62, row_bot), "R")

        # ---- BUTTONS (ABXY) ----
        # Center of cluster aligns with Top Row
        btn_center_x = w * 0.75
        btn_center_y = row_top
        spacing = 28

        self._draw_button(p, QPointF(btn_center_x, btn_center_y - spacing), "Y")
        self._draw_button(p, QPointF(btn_center_x + spacing, btn_center_y), "B")
        self._draw_button(p, QPointF(btn_center_x - spacing, btn_center_y), "X")
        self._draw_button(p, QPointF(btn_center_x, btn_center_y + spacing), "A")

        # ---- DPAD ----
        # Center aligns with Bottom Row
        dpad_center_x = w * 0.40
        dpad_center_y = row_bot
        dpad_dist = 20

        self._draw_dpad_btn(p, QPointF(dpad_center_x, dpad_center_y - dpad_dist), "DPAD_UP")
        self._draw_dpad_btn(p, QPointF(dpad_center_x, dpad_center_y + dpad_dist), "DPAD_DOWN")
        self._draw_dpad_btn(p, QPointF(dpad_center_x - dpad_dist, dpad_center_y), "DPAD_LEFT")
        self._draw_dpad_btn(p, QPointF(dpad_center_x + dpad_dist, dpad_center_y), "DPAD_RIGHT")

        # ---- CENTER BUTTONS (START / BACK) ----
        # Aligned with Top Row
        center_spacing = w * 0.08

        self._draw_small_button(p, QPointF(w * 0.5 - center_spacing, row_top), "BACK")
        self._draw_small_button(p, QPointF(w * 0.5 + center_spacing, row_top), "START")

    # ================= HELPERS =================

    def _draw_button(self, p: QPainter, pos: QPointF, name: str):
        value = self.buttons.get(name, 0.0)
        r = 13

        color = self._inactive
        if value > 0:
            color = self._blend(self._inactive, self._active, value)

        p.setPen(QPen(self._outline, 1))
        p.setBrush(color)
        p.drawEllipse(pos, r, r)

    def _draw_small_button(self, p: QPainter, pos: QPointF, name: str):
        value = self.buttons.get(name, 0.0)
        r = 8

        color = self._inactive
        if value > 0:
            color = self._blend(self._inactive, self._active, value)

        p.setPen(QPen(self._outline, 1))
        p.setBrush(color)
        p.drawEllipse(pos, r, r)

    def _draw_dpad_btn(self, p: QPainter, center: QPointF, name: str):
        value = self.buttons.get(name, 0.0)
        size = 18

        color = self._inactive
        if value > 0:
            color = self._blend(self._inactive, self._active, value)

        p.setPen(QPen(self._outline, 1))
        p.setBrush(color)

        rect = QRectF(center.x() - size / 2, center.y() - size / 2, size, size)
        p.drawRoundedRect(rect, 2, 2)

    def _draw_bumper(self, p: QPainter, pos: QPointF, name: str):
        value = self.buttons.get(name, 0.0)
        w, h = 60, 16

        rect_x = pos.x() - w / 2
        rect_y = pos.y() - h / 2

        color = self._inactive
        if value > 0:
            color = self._blend(self._inactive, self._active, value)

        p.setPen(QPen(self._outline, 1))
        p.setBrush(color)
        p.drawRoundedRect(rect_x, rect_y, w, h, 4, 4)

    def _draw_stick(self, p: QPainter, center: QPointF, stick: str):


        radius = 34

        pressed = self.buttons.get(
            "LS" if stick == "L" else "RS",
            0.0
        )

        outline = self._outline
        if pressed:
            outline = self._blend(self._outline, self._active, pressed)

        p.setPen(QPen(outline, 2))
        p.setBrush(self._inactive)
        p.drawEllipse(center, radius, radius)



        x, y = self.sticks.get(stick, (0.0, 0.0))

        p.setPen(QPen(self._outline, 1))
        p.setBrush(self._inactive)
        p.drawEllipse(center, radius, radius)

        p.setPen(QPen(self._axis, 1))
        p.drawLine(center.x() - radius, center.y(),
                   center.x() + radius, center.y())
        p.drawLine(center.x(), center.y() - radius,
                   center.x(), center.y() + radius)

        dot = QPointF(
            center.x() + x * radius,
            center.y() - y * radius
        )

        p.setBrush(self._active)
        p.setPen(Qt.NoPen)
        p.drawEllipse(dot, 8, 8)





    def _draw_trigger(self, p: QPainter, pos: QPointF, name: str):
        value = self.triggers.get(name, 0.0)
        w, h = 64, 10

        p.setPen(QPen(self._outline, 1))
        p.setBrush(self._inactive)
        p.drawRoundedRect(pos.x() - w / 2, pos.y(), w, h, 2, 2)

        if value > 0:
            p.setBrush(self._active)
            p.drawRoundedRect(
                pos.x() - w / 2,
                pos.y(),
                w * value,
                h,
                2,
                2
            )

    def _blend(self, c1: QColor, c2: QColor, t: float) -> QColor:
        return QColor(
            int(c1.red() + (c2.red() - c1.red()) * t),
            int(c1.green() + (c2.green() - c1.green()) * t),
            int(c1.blue() + (c2.blue() - c1.blue()) * t),
        )