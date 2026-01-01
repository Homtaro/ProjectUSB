from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from frontend.style.theme import *

from frontend.panels.hwTests.keyboard.multiTestKeyboard import KeyboardMultiTestWindow
from frontend.panels.hwTests.mouse.multiTestMouse import MouseMultiTestWindow
from frontend.panels.hwTests.gamepad.multiTestGamepad import GamepadMultiTestWindow
from frontend.panels.hwTests.audio.audioOut import AudioOutputTestWindow
from frontend.panels.hwTests.audio.audioIn import AudioInputTestWindow
from frontend.panels.hwTests.storage.singleFileTest import SingleFileStorageTestWindow
from frontend.panels.hwTests.storage.multiFileTest import MultiFileStorageTestWindow


ACCENT_COLOR = "#0078d7"


# -----------------------------
# Left-side category button
# -----------------------------
class DeviceCategoryButton(QPushButton):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(42)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFont(QFont("Segoe UI", 10))

        self.setStyleSheet(self._style(False))

    def set_active(self, active: bool):
        self.setChecked(active)
        self.setStyleSheet(self._style(active))

    def _style(self, active: bool):
        bg = BG_HOVER if active else "transparent"
        border = ACCENT if active else "transparent"

        return f"""
            QPushButton {{
                background-color: {bg};
                border: none;
                border-left: 3px solid {border};
                text-align: left;
                padding-left: 10px;
                color: {TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {BG_HOVER};
            }}
        """


# -----------------------------
# Windows-style test tile
# -----------------------------
class TestTile(QFrame):
    def __init__(self, title: str, description: str, on_click=None, parent=None):
        super().__init__(parent)
        self.on_click = on_click
        self.setFixedSize(200, 110)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: none;
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: #252525;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI Semibold", 12))
        title_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                background-color: transparent;
            }
        """)

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                background-color: transparent;
            }
        """)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch(1)

    def mousePressEvent(self, event):
        if self.on_click:
            self.on_click()
        super().mousePressEvent(event)

# -----------------------------
# Main Hardware Tests Panel
# -----------------------------
class HardwareTests(QWidget):
    def __init__(self, backend, parent=None,):
        super().__init__(parent)
        self.backend = backend
        #self.setStyleSheet("background-color: #121212;")

        self.test_windows = {
            ("Keyboard", "Multitest"): KeyboardMultiTestWindow,
            ("Mouse", "Multitest"): MouseMultiTestWindow,
            ("Gamepad (X-Input)", "Multitest"): GamepadMultiTestWindow,
            ("Audio", "Playback Test"): AudioOutputTestWindow,
            ("Audio", "Microphone Test"): AudioInputTestWindow,
            ("Storage", "Singular file test"): SingleFileStorageTestWindow,
            ("Storage", "Multiple files test"): MultiFileStorageTestWindow,
        }

        #self._open_windows = []
        self._open_windows = {}

        self.category_buttons = {}
        self.tiles_layout = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # =========================
        # LEFT PANEL
        # =========================
        left_panel = QFrame()
        left_panel.setFixedWidth(260)
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #1b1b1b;
                border-right: 1px solid #2a2a2a;
            }
        """)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 16, 12, 16)
        left_layout.setSpacing(8)

        title = QLabel("Devices")
        title.setFont(QFont("Segoe UI Semibold", 18))
        title.setStyleSheet("color: #ffffff;")

        left_layout.addWidget(title)
        left_layout.addSpacing(10)

        # Category -> tests mapping
        self.tests_by_category = {
            "Keyboard": [
                ("Multitest", "NKRO, Heatmap"),
            ],
            "Mouse": [
                ("Multitest", "Heatmap, Polling Rate, Jitter"),
            ],
            "Gamepad (X-Input)": [
                ("Multitest", "Heatmap, Stick Info, Circular Error"),
            ],
            "Audio": [
                ("Playback Test", "Left / right channels"),
                ("Microphone Test", "Record & playback"),
            ],
            "Storage": [
                ("Singular file test", "Read / write benchmark with hash verification"),
                ("Multiple files test", "Read / write benchmark with hash verification"),
            ]
        }

        for cat in self.tests_by_category.keys():
            btn = DeviceCategoryButton(cat)
            btn.clicked.connect(lambda _, c=cat: self.select_category(c))
            self.category_buttons[cat] = btn
            left_layout.addWidget(btn)

        left_layout.addStretch(1)

        # =========================
        # RIGHT PANEL
        # =========================
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(32, 24, 32, 24)
        right_layout.setSpacing(16)

        right_panel.setStyleSheet("background-color: transparent;")

        self.header = QLabel("Select a test")
        self.header.setFont(QFont("Segoe UI Semibold", 22))
        self.header.setStyleSheet("color: #ffffff;")

        self.sub = QLabel("Choose a diagnostic test")
        self.sub.setFont(QFont("Segoe UI", 11))
        self.sub.setStyleSheet("color: #9a9a9a;")

        right_layout.addWidget(self.header)
        right_layout.addWidget(self.sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll.setStyleSheet("""
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 4px;
            }
        """)

        scroll_content = QWidget()
        #self.tiles_layout = QHBoxLayout(scroll_content)
        #self.tiles_layout.setSpacing(20)
        #self.tiles_layout.setContentsMargins(0, 10, 0, 10)
        #self.tiles_layout.addStretch(1)

        self.tiles_layout = QGridLayout(scroll_content)
        self.tiles_layout.setSpacing(20)
        self.tiles_layout.setContentsMargins(0, 10, 0, 10)
        self.tiles_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)



        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll, 1)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)

        # Default category
        self.select_category("Keyboard")

    def close_all_test_windows(self):
        for w in list(self._open_windows.values()):
            if w:
                w.close()
        self._open_windows.clear()

    # -----------------------------
    # Category selection logic
    # -----------------------------
    def select_category(self, category: str):
        for cat, btn in self.category_buttons.items():
            btn.set_active(cat == category)

        self.header.setText(category)
        self.sub.setText("Available tests")

        self._populate_tiles(self.tests_by_category.get(category, []))

    # def _populate_tiles(self, tests):
    #     while self.tiles_layout.count() > 1:
    #         item = self.tiles_layout.takeAt(0)
    #         if item.widget():
    #             item.widget().deleteLater()
    #
    #     for title, desc in tests:
    #         self.tiles_layout.insertWidget(
    #             self.tiles_layout.count() - 1,
    #             TestTile(title, desc)
    #         )

    # def _populate_tiles(self, tests):
    #     # Clear old tiles
    #     while self.tiles_layout.count():
    #         item = self.tiles_layout.takeAt(0)
    #         if item.widget():
    #             item.widget().deleteLater()
    #
    #     columns = 3  # adjust for taste (2–4 works well)
    #     row = 0
    #     col = 0
    #
    #     for title, desc in tests:
    #         tile = TestTile(title, desc)
    #         self.tiles_layout.addWidget(tile, row, col)
    #
    #         col += 1
    #         if col >= columns:
    #             col = 0
    #             row += 1

    def _populate_tiles(self, tests):
        while self.tiles_layout.count():
            item = self.tiles_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        columns = 3
        row = col = 0

        for title, desc in tests:
            key = (self.header.text(), title)
            window_cls = self.test_windows.get(key)

            def open_window(cls=window_cls, key=key):
                if not cls:
                    return

                if key in self._open_windows:
                    w = self._open_windows[key]
                    w.raise_()
                    w.activateWindow()
                    return

                w = cls()
                w.setWindowFlag(Qt.Window)
                w.setAttribute(Qt.WA_DeleteOnClose, True)

                def on_close(event, k=key):
                    self._open_windows.pop(k, None)
                    event.accept()

                w.closeEvent = on_close

                self._open_windows[key] = w

                w.show()
                w.raise_()
                w.activateWindow()


                w.destroyed.connect(lambda _, k=key: self._open_windows.pop(k, None))

                self._open_windows[key] = w

            tile = TestTile(title, desc, on_click=open_window)
            self.tiles_layout.addWidget(tile, row, col)

            col += 1
            if col >= columns:
                col = 0
                row += 1
