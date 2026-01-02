from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class KeyWidget(QLabel):
    def __init__(self, text: str, scancode: int):
        super().__init__(text)
        self.scancode = scancode
        self.press_count = 0

        self.setMinimumSize(48, 48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setAlignment(Qt.AlignCenter)
        #self.setFixedSize(48, 48)
        self.setStyleSheet(self._base_style("#1e1e1e"))

    def _base_style(self, color: str):
        return f"""
        QLabel {{
            background-color: {color};
            border: 1px solid #333;
            border-radius: 6px;
            color: #e0e0e0;
            font-size: 11px;
        }}
        """

    def key_down(self):
        self.press_count += 1
        self.setStyleSheet(self._base_style("#3daee9"))

    def key_up(self):
        self.setStyleSheet(self._base_style("#1e1e1e"))

    def set_heat(self, intensity: float):
        # intensity: 0..1
        red = int(255 * intensity)
        color = QColor(red, 50, 50)
        self.setStyleSheet(self._base_style(color.name()))

    def reset(self):
        self.press_count = 0
        self.setStyleSheet(self._base_style("#1e1e1e"))

class KeyboardVisualPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.keys = {}  # scancode -> KeyWidget

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        layout = QGridLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)

        layout.setColumnStretch(0, 0)
        layout.setRowStretch(0, 0)

        KEY_W = 48  # base key width
        KEY_H = 48

        for col in range(0, 26):
            layout.setColumnMinimumWidth(col, KEY_W)

        for row in range(0, 7):
            layout.setRowMinimumHeight(row, KEY_H)

        SPACER = 24

        for col in (1, 6, 11, 16, 20):
            layout.setColumnMinimumWidth(col, SPACER)

        for col in (10, 11, 12, 13):
            layout.setColumnMinimumWidth(col, SPACER)

        self._build_layout(layout)

    def _add_key(self, layout, row, col, label, scancode, col_span=1):
        key = KeyWidget(label, scancode)
        layout.addWidget(key, row, col, 1, col_span)
        self.keys[scancode] = key

    def _build_layout(self, layout):
        r = 0

        # ===== Row 0 — Esc + F-keys =====
        self._add_key(layout, r, 0, "ESC", 0x01)
        self._add_key(layout, r, 2, "F1", 0x3B)
        self._add_key(layout, r, 3, "F2", 0x3C)
        self._add_key(layout, r, 4, "F3", 0x3D)
        self._add_key(layout, r, 5, "F4", 0x3E)
        self._add_key(layout, r, 7, "F5", 0x3F)
        self._add_key(layout, r, 8, "F6", 0x40)
        self._add_key(layout, r, 9, "F7", 0x41)
        self._add_key(layout, r, 10, "F8", 0x42)
        self._add_key(layout, r, 12, "F9", 0x43)
        self._add_key(layout, r, 13, "F10", 0x44)
        self._add_key(layout, r, 14, "F11", 0x57)
        self._add_key(layout, r, 15, "F12", 0x58)

        # ===== Navigation cluster (top) =====
        self._add_key(layout, 0, 17, "PRT", 0xE037)
        self._add_key(layout, 0, 18, "SCR", 0x46)
        self._add_key(layout, 0, 19, "PAUSE", 0xE11D)

        # ===== Row 1 — Number row =====
        r += 1
        self._add_key(layout, r, 0, "`", 0x29)
        self._add_key(layout, r, 1, "1", 0x02)
        self._add_key(layout, r, 2, "2", 0x03)
        self._add_key(layout, r, 3, "3", 0x04)
        self._add_key(layout, r, 4, "4", 0x05)
        self._add_key(layout, r, 5, "5", 0x06)
        self._add_key(layout, r, 6, "6", 0x07)
        self._add_key(layout, r, 7, "7", 0x08)
        self._add_key(layout, r, 8, "8", 0x09)
        self._add_key(layout, r, 9, "9", 0x0A)
        self._add_key(layout, r, 10, "0", 0x0B)
        self._add_key(layout, r, 11, "-", 0x0C)
        self._add_key(layout, r, 12, "=", 0x0D)
        self._add_key(layout, r, 13, "BACK", 0x0E, 3)

        # ===== Row 2 — Q row =====
        r += 1
        self._add_key(layout, r, 0, "TAB", 0x0F, 2)
        self._add_key(layout, r, 2, "Q", 0x10)
        self._add_key(layout, r, 3, "W", 0x11)
        self._add_key(layout, r, 4, "E", 0x12)
        self._add_key(layout, r, 5, "R", 0x13)
        self._add_key(layout, r, 6, "T", 0x14)
        self._add_key(layout, r, 7, "Y", 0x15)
        self._add_key(layout, r, 8, "U", 0x16)
        self._add_key(layout, r, 9, "I", 0x17)
        self._add_key(layout, r, 10, "O", 0x18)
        self._add_key(layout, r, 11, "P", 0x19)
        self._add_key(layout, r, 12, "[", 0x1A)
        self._add_key(layout, r, 13, "]", 0x1B)
        self._add_key(layout, r, 14, "\\", 0x2B, 2)

        # ===== Navigation cluster =====
        self._add_key(layout, 1, 17, "INS", 0xE052)
        self._add_key(layout, 1, 18, "HOME", 0xE047)
        self._add_key(layout, 1, 19, "PGUP", 0xE049)

        self._add_key(layout, 2, 17, "DEL", 0xE053)
        self._add_key(layout, 2, 18, "END", 0xE04F)
        self._add_key(layout, 2, 19, "PGDN", 0xE051)

        # ===== Arrow keys =====
        self._add_key(layout, 4, 18, "↑", 0xE048)
        self._add_key(layout, 5, 17, "←", 0xE04B)
        self._add_key(layout, 5, 18, "↓", 0xE050)
        self._add_key(layout, 5, 19, "→", 0xE04D)

        # ===== Row 3 — A row =====
        r += 1
        self._add_key(layout, r, 0, "CAPS", 0x3A, 2)
        self._add_key(layout, r, 2, "A", 0x1E)
        self._add_key(layout, r, 3, "S", 0x1F)
        self._add_key(layout, r, 4, "D", 0x20)
        self._add_key(layout, r, 5, "F", 0x21)
        self._add_key(layout, r, 6, "G", 0x22)
        self._add_key(layout, r, 7, "H", 0x23)
        self._add_key(layout, r, 8, "J", 0x24)
        self._add_key(layout, r, 9, "K", 0x25)
        self._add_key(layout, r, 10, "L", 0x26)
        self._add_key(layout, r, 11, ";", 0x27)
        self._add_key(layout, r, 12, "'", 0x28)
        self._add_key(layout, r, 13, "ENTER", 0x1C, 3)

        # ===== Row 4 — Z row =====
        r += 1
        self._add_key(layout, r, 0, "SHIFT", 0x2A, 3)
        self._add_key(layout, r, 3, "Z", 0x2C)
        self._add_key(layout, r, 4, "X", 0x2D)
        self._add_key(layout, r, 5, "C", 0x2E)
        self._add_key(layout, r, 6, "V", 0x2F)
        self._add_key(layout, r, 7, "B", 0x30)
        self._add_key(layout, r, 8, "N", 0x31)
        self._add_key(layout, r, 9, "M", 0x32)
        self._add_key(layout, r, 10, ",", 0x33)
        self._add_key(layout, r, 11, ".", 0x34)
        self._add_key(layout, r, 12, "/", 0x35)
        self._add_key(layout, r, 13, "SHIFT", 0x36, 3)

        # ===== Row 5 — Bottom row =====
        r += 1
        self._add_key(layout, r, 0, "CTRL", 0x1D, 2)
        self._add_key(layout, r, 2, "WIN", 0xE05B)
        self._add_key(layout, r, 3, "ALT", 0x38)
        self._add_key(layout, r, 4, "SPACE", 0x39, 6)
        self._add_key(layout, r, 10, "ALT", 0x38 | 0xE000,1)
        self._add_key(layout, r, 11, "WIN", 0xE05C,1)
        self._add_key(layout, r, 12, "MENU", 0xE05D,1)
        self._add_key(layout, r, 13, "CTRL", 0x1D | 0xE000,3)

        # ===== Numpad =====
        self._add_key(layout, 1, 21, "NUM", 0x45)
        self._add_key(layout, 1, 22, "/", 0xE035)
        self._add_key(layout, 1, 23, "*", 0x37)
        self._add_key(layout, 1, 24, "-", 0x4A)

        self._add_key(layout, 2, 21, "7", 0x47)
        self._add_key(layout, 2, 22, "8", 0x48)
        self._add_key(layout, 2, 23, "9", 0x49)
        #self._add_key(layout, 2, 24, "+", 0x4E, 2)

        self._add_key(layout, 3, 21, "4", 0x4B)
        self._add_key(layout, 3, 22, "5", 0x4C)
        self._add_key(layout, 3, 23, "6", 0x4D)

        self._add_key(layout, 4, 21, "1", 0x4F)
        self._add_key(layout, 4, 22, "2", 0x50)
        self._add_key(layout, 4, 23, "3", 0x51)
        #self._add_key(layout, 4, 24, "ENTER", 0x1C, 2)

        self._add_key(layout, 5, 21, "0", 0x52, 2)
        self._add_key(layout, 5, 23, ".", 0x53)


        #Manual resizing

        # PLUS (row 2–3)
        layout.addWidget(KeyWidget("+", 0x4E), 2, 24, 2, 1)

        # ENTER (row 4–5)
        layout.addWidget(KeyWidget("ENTER", 0xE01C), 4, 24, 2, 1)

        #Manual wiring

        self.keys[0xE01C] = layout.itemAtPosition(4, 24).widget()
        self.keys[0x4E] = layout.itemAtPosition(2, 24).widget()


    # === API exposed to tests ===

    def key_down(self, scancode: int):
        key = self.keys.get(scancode)
        if key:
            key.key_down()

    def key_up(self, scancode: int):
        key = self.keys.get(scancode)
        if key:
            key.key_up()

    def reset(self):
        for key in self.keys.values():
            key.reset()
