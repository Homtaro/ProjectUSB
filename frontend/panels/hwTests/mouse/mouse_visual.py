# frontend/panels/hwTests/mouse/mouse_visual.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class HeatButton(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.count = 0
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(40, 40)
        self._set_color("#1e1e1e")

    def _set_color(self, color):
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 8px;
                border: 1px solid #333;
                color: #e0e0e0;
                font-weight: bold;
            }}
        """)

    def hit(self):
        self.count += 1
        intensity = min(self.count / 40, 1.0)
        red = int(255 * intensity)
        self._set_color(QColor(red, 70, 70).name())

    def reset(self):
        self.count = 0
        self._set_color("#1e1e1e")


class MouseVisualPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.buttons = {}

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(8)

        # ================= MOUSE BODY =================
        body = QWidget()
        body.setFixedSize(160, 240)
        body.setStyleSheet("""
            QWidget {
                background-color: #141414;
                border-radius: 80px;
                border: 2px solid #333;
            }
        """)

        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 24, 16, 16)
        body_layout.setSpacing(1)

        # === Top buttons ===
        top = QHBoxLayout()
        self.buttons["left"] = HeatButton("M1")
        self.buttons["right"] = HeatButton("M2")
        top.addWidget(self.buttons["left"])
        top.addWidget(self.buttons["right"])

        # === Wheel ===
        self.buttons["wheel_up"] = HeatButton("▲")
        self.buttons["middle"] = HeatButton("●")
        self.buttons["wheel_down"] = HeatButton("▼")

        body_layout.addLayout(top)
        body_layout.addWidget(self.buttons["wheel_up"], alignment=Qt.AlignCenter)
        body_layout.addWidget(self.buttons["middle"], alignment=Qt.AlignCenter)
        body_layout.addWidget(self.buttons["wheel_down"], alignment=Qt.AlignCenter)

        root.addWidget(body, alignment=Qt.AlignCenter)

        # ================= SIDE BUTTONS =================
        sides = QHBoxLayout()
        self.buttons["x1"] = HeatButton("X1")
        self.buttons["x2"] = HeatButton("X2")
        sides.addWidget(self.buttons["x1"])
        sides.addSpacing(24)
        sides.addWidget(self.buttons["x2"])

        root.addLayout(sides)

    # === API ===
    def button_hit(self, name):
        btn = self.buttons.get(name)
        if btn:
            btn.hit()

    def reset(self):
        for btn in self.buttons.values():
            btn.reset()
