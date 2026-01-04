from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QRadialGradient
from PySide6.QtCore import Qt, QPointF, QRectF


class GamepadVisual(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)

        # State storage
        self.buttons = {
            "A": False, "B": False, "X": False, "Y": False,
            "LB": False, "RB": False,
            "BACK": False, "START": False, "GUIDE": False,
            "LS": False, "RS": False,  # Stick clicks
            "DPAD_UP": False, "DPAD_DOWN": False, "DPAD_LEFT": False, "DPAD_RIGHT": False
        }

        self.axes = {
            "LX": 0.0, "LY": 0.0,
            "RX": 0.0, "RY": 0.0,
            "LT": 0.0, "RT": 0.0
        }

        # Colors
        self.col_body = QColor("#2d2d2d")
        self.col_body_outline = QColor("#111")
        self.col_btn_off = QColor("#444")
        self.col_highlight = QColor("#3aa675")  # Greenish highlight
        self.col_text = QColor("#eee")

        # Specific Xbox Colors
        self.col_a = QColor("#4dbd74")
        self.col_b = QColor("#e74c3c")
        self.col_x = QColor("#3498db")
        self.col_y = QColor("#f1c40f")

    def update_state(self, buttons: dict, axes: dict):
        """
        Update visual state.
        buttons: dict of name -> bool
        axes: dict of name -> float (-1.0 to 1.0 for sticks, 0.0 to 1.0 for triggers)
        """
        changed = False
        for k, v in buttons.items():
            if k in self.buttons and self.buttons[k] != v:
                self.buttons[k] = v
                changed = True

        for k, v in axes.items():
            if k in self.axes and abs(self.axes[k] - v) > 0.01:
                self.axes[k] = v
                changed = True

        if changed:
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Setup Scaling (Logical Canvas: 800x600)
        w, h = self.width(), self.height()
        scale = min(w / 800, h / 600)

        # Center the gamepad in the widget
        dx = (w - 800 * scale) / 2
        dy = (h - 600 * scale) / 2

        painter.translate(dx, dy)
        painter.scale(scale, scale)

        # 2. Draw Components
        self._draw_triggers(painter)
        self._draw_bumpers(painter)
        self._draw_body(painter)
        self._draw_dpad(painter)
        self._draw_sticks(painter)
        self._draw_face_buttons(painter)
        self._draw_center_buttons(painter)

    def _draw_body(self, p: QPainter):
        path = QPainterPath()
        # Main chassis shape approximation
        path.moveTo(200, 150)
        path.lineTo(600, 150)
        path.cubicTo(750, 150, 750, 450, 600, 500)  # Right handle
        path.cubicTo(500, 520, 300, 520, 200, 500)  # Bottom curve
        path.cubicTo(50, 450, 50, 150, 200, 150)  # Left handle

        p.setPen(QPen(self.col_body_outline, 4))
        p.setBrush(self.col_body)
        p.drawPath(path)

    def _draw_triggers(self, p: QPainter):
        # LT
        self._draw_trigger_bar(p, 180, 80, self.axes["LT"])
        # RT
        self._draw_trigger_bar(p, 520, 80, self.axes["RT"])

    def _draw_trigger_bar(self, p: QPainter, x, y, val):
        # Background
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#222"))
        p.drawRoundedRect(x, y, 100, 40, 8, 8)

        # Fill
        if val > 0.01:
            fill_h = 40 * val
            p.setBrush(self.col_highlight)
            # Fill from bottom up usually
            p.drawRoundedRect(x, y, 100 * val, 40, 8, 8)

            # Text
            p.setPen(Qt.white)
            p.drawText(x, y, 100, 40, Qt.AlignCenter, f"{val:.2f}")

    def _draw_bumpers(self, p: QPainter):
        # LB
        color = self.col_highlight if self.buttons["LB"] else self.col_btn_off
        p.setBrush(color)
        p.setPen(QPen(Qt.black, 2))
        p.drawRoundedRect(180, 130, 120, 30, 5, 5)
        p.setPen(Qt.white)
        p.drawText(180, 130, 120, 30, Qt.AlignCenter, "LB")

        # RB
        color = self.col_highlight if self.buttons["RB"] else self.col_btn_off
        p.setBrush(color)
        p.setPen(QPen(Qt.black, 2))
        p.drawRoundedRect(500, 130, 120, 30, 5, 5)
        p.setPen(Qt.white)
        p.drawText(500, 130, 120, 30, Qt.AlignCenter, "RB")

    def _draw_dpad(self, p: QPainter):
        cx, cy = 280, 350
        size = 40

        # Cross shape
        path = QPainterPath()
        path.addRect(cx - size / 2, cy - size * 1.5, size, size * 3)  # Vertical
        path.addRect(cx - size * 1.5, cy - size / 2, size * 3, size)  # Horizontal

        p.setPen(QPen(Qt.black, 2))
        p.setBrush(self.col_btn_off)
        p.drawPath(path)

        # Highlights
        p.setBrush(self.col_highlight)
        p.setPen(Qt.NoPen)

        if self.buttons["DPAD_UP"]:
            p.drawRect(cx - size / 2, cy - size * 1.5, size, size)
        if self.buttons["DPAD_DOWN"]:
            p.drawRect(cx - size / 2, cy + size * 0.5, size, size)
        if self.buttons["DPAD_LEFT"]:
            p.drawRect(cx - size * 1.5, cy - size / 2, size, size)
        if self.buttons["DPAD_RIGHT"]:
            p.drawRect(cx + size * 0.5, cy - size / 2, size, size)

    def _draw_sticks(self, p: QPainter):
        # Left Stick
        self._draw_single_stick(p, 200, 250, self.axes["LX"], -self.axes["LY"], self.buttons["LS"])

        # Right Stick
        self._draw_single_stick(p, 520, 350, self.axes["RX"], -self.axes["RY"], self.buttons["RS"])

    def _draw_single_stick(self, p: QPainter, cx, cy, x_val, y_val, clicked):
        radius = 45

        # Base
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1a1a1a"))
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        # Stick Cap position (clamped visual movement)
        move_scale = 25
        sx = cx + (x_val * move_scale)
        sy = cy + (y_val * move_scale)

        # Cap
        grad = QRadialGradient(sx - 10, sy - 10, 50)
        if clicked:
            grad.setColorAt(0, QColor("#555"))
            grad.setColorAt(1, QColor("#333"))
            p.setBrush(QColor("#5a8"))  # Green tint when clicked
        else:
            grad.setColorAt(0, QColor("#444"))
            grad.setColorAt(1, QColor("#222"))
            p.setBrush(grad)

        p.setPen(QPen(Qt.black, 1))
        p.drawEllipse(QPointF(sx, sy), 30, 30)

    def _draw_face_buttons(self, p: QPainter):
        cx, cy = 580, 230
        dist = 45

        # Y (Top)
        self._draw_circle_btn(p, cx, cy - dist, "Y", self.col_y, self.buttons["Y"])
        # B (Right)
        self._draw_circle_btn(p, cx + dist, cy, "B", self.col_b, self.buttons["B"])
        # A (Bottom)
        self._draw_circle_btn(p, cx, cy + dist, "A", self.col_a, self.buttons["A"])
        # X (Left)
        self._draw_circle_btn(p, cx - dist, cy, "X", self.col_x, self.buttons["X"])

    def _draw_circle_btn(self, p: QPainter, x, y, label, color, pressed):
        p.setPen(QPen(Qt.black, 2))

        if pressed:
            p.setBrush(color.lighter(130))  # Brighten when pressed
        else:
            p.setBrush(color.darker(150))  # Dim when not

        p.drawEllipse(QPointF(x, y), 20, 20)

        p.setPen(Qt.white if not pressed else Qt.black)
        font = p.font()
        font.setBold(True)
        p.setFont(font)
        p.drawText(QRectF(x - 20, y - 20, 40, 40), Qt.AlignCenter, label)

    def _draw_center_buttons(self, p: QPainter):
        # Back
        self._draw_small_btn(p, 330, 250, "<", self.buttons["BACK"])
        # Guide
        self._draw_big_guide_btn(p, 400, 220, self.buttons["GUIDE"])
        # Start
        self._draw_small_btn(p, 470, 250, ">", self.buttons["START"])

    def _draw_small_btn(self, p: QPainter, x, y, label, pressed):
        p.setPen(QPen(Qt.black, 1))
        p.setBrush(self.col_highlight if pressed else self.col_btn_off)
        p.drawEllipse(QPointF(x, y), 12, 12)

    def _draw_big_guide_btn(self, p: QPainter, x, y, pressed):
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(Qt.white if pressed else QColor("#333"))
        p.drawEllipse(QPointF(x, y), 25, 25)

        # "X" Logo approximation
        p.setPen(QPen(self.col_highlight if pressed else QColor("#555"), 3))
        p.drawLine(x - 10, y - 10, x + 10, y + 10)
        p.drawLine(x + 10, y - 10, x - 10, y + 10)