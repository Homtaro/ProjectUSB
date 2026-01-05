from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from frontend.journal.details.audio_input_view import AudioInputTestView
from frontend.journal.details.gamepad_multitest_view import GamepadMultiTestView
from frontend.journal.details.keyboard_multitest_view import KeyboardMultiTestView
from frontend.journal.details.mouse_multitest_view import MouseMultiTestView
from frontend.journal.details.storage_MultiFile_View import StorageMultiFileTestView
from frontend.journal.details.storage_SingleFile_view import StorageSingleFileTestView
from frontend.journal.journal_loader import load_journal_entries
from frontend.style.theme import *


# --------------------------------
# Single journal entry widget
# --------------------------------
class JournalEntryItem(QFrame):
    clicked = Signal(object)  # emits JournalEntry

    def __init__(self, entry, parent=None):
        super().__init__(parent)
        self.entry = entry

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(88)

        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: #252525;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        top = QLabel(f"{entry.date} • {entry.category}")
        top.setFont(QFont("Segoe UI", 9))
        top.setStyleSheet(f"color: {TEXT_MUTED};")

        name = QLabel(entry.device_name)
        name.setFont(QFont("Segoe UI Semibold", 10))
        name.setStyleSheet(f"color: {TEXT_PRIMARY};")

        meta = QLabel(f"{entry.test_name}   |   {entry.pid_vid}")
        meta.setFont(QFont("Segoe UI", 9))
        meta.setStyleSheet(f"color: {TEXT_SECONDARY};")

        layout.addWidget(top)
        layout.addWidget(name)
        layout.addWidget(meta)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.entry)
        super().mousePressEvent(event)


# --------------------------------
# Journal panel
# --------------------------------
class JournalPanel(QWidget):
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend

        self.all_entries = []
        self.visible_entries = []

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ============================
        # LEFT PANEL
        # ============================
        left_panel = QFrame()
        left_panel.setFixedWidth(380)
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #1b1b1b;
            }
        """)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        title = QLabel("Test Journal")
        title.setFont(QFont("Segoe UI Semibold", 18))
        title.setStyleSheet("color: white;")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search device, test, PID/VID...")
        self.search.setFixedHeight(34)
        self.search.setStyleSheet("""
            QLineEdit {
                background-color: #222;
                border: 1px solid #2d2d2d;
                border-radius: 6px;
                padding: 6px;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
        """)

        # ---- Filters row
        filters = QHBoxLayout()
        filters.setSpacing(8)

        self.sort_box = QComboBox()
        self.sort_box.addItems(["Newest first", "Oldest first"])
        self.sort_box.setFixedHeight(30)

        self.category_box = QComboBox()
        self.category_box.addItems([
            "All categories",
            "Keyboard",
            "Mouse",
            "Gamepad",
            "Audio",
            "Storage"
        ])
        self.category_box.setFixedHeight(30)

        self.test_box = QComboBox()
        self.test_box.addItems([
            "All tests",
            "Multitest",
            "AudioInputTest",
            "StorageMultiFileTest",
            "StorageSingleFileTest"
        ])
        self.test_box.setFixedHeight(30)

        for box in (self.sort_box, self.category_box, self.test_box):
            box.setStyleSheet("""
                QComboBox {
                    background-color: #222;
                    border: 1px solid #2d2d2d;
                    border-radius: 6px;
                    padding: 4px 6px;
                    color: #ffffff;
                }
            """)

        filters.addWidget(self.sort_box)
        filters.addWidget(self.category_box)
        filters.addWidget(self.test_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.journal_layout = QVBoxLayout(container)
        self.journal_layout.setSpacing(10)
        self.journal_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(container)

        left_layout.addWidget(title)
        left_layout.addWidget(self.search)
        left_layout.addLayout(filters)
        left_layout.addWidget(scroll, 1)

        # ============================
        # RIGHT PANEL
        # ============================
        right_panel = QFrame()
        self.right_layout = QVBoxLayout(right_panel)
        self.right_layout.setContentsMargins(32, 24, 32, 24)
        self.right_layout.setSpacing(16)

        self.placeholder = QLabel("Select a test entry")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setFont(QFont("Segoe UI", 14))
        self.placeholder.setStyleSheet("color: #555;")

        self.right_layout.addStretch(1)
        self.right_layout.addWidget(self.placeholder)
        self.right_layout.addStretch(2)

        # ============================
        # ASSEMBLY
        # ============================
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)

        # ============================
        # SIGNALS
        # ============================
        self.search.textChanged.connect(self.apply_filters)
        self.sort_box.currentIndexChanged.connect(self.apply_filters)
        self.category_box.currentIndexChanged.connect(self.apply_filters)
        self.test_box.currentIndexChanged.connect(self.apply_filters)

        self.load_entries()

    # --------------------------------
    # Journal logic
    # --------------------------------
    def load_entries(self):
        self.all_entries = load_journal_entries(Path.cwd() / "journal")
        self.apply_filters()

    def refresh(self):
        self.load_entries()

    def clear_journal_list(self):
        while self.journal_layout.count():
            item = self.journal_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def apply_filters(self):
        query = self.search.text().lower().strip()
        category = self.category_box.currentText()
        test_filter = self.test_box.currentText()
        newest_first = self.sort_box.currentIndex() == 0

        filtered = []

        for entry in self.all_entries:
            if query:
                haystack = f"{entry.device_name} {entry.test_name} {entry.pid_vid}".lower()
                if query not in haystack:
                    continue

            if category != "All categories" and entry.category != category:
                continue

            if test_filter != "All tests" and test_filter.lower() not in entry.test_name.lower():
                continue

            filtered.append(entry)

        filtered.sort(key=lambda e: e.timestamp, reverse=newest_first)

        self.visible_entries = filtered
        self.rebuild_journal_view()

    def rebuild_journal_view(self):
        self.clear_journal_list()

        for entry in self.visible_entries:
            item = JournalEntryItem(entry)
            item.clicked.connect(self.show_entry)
            self.journal_layout.addWidget(item)

        self.journal_layout.addStretch(1)

    # --------------------------------
    # Right panel
    # --------------------------------
    def clear_right_panel(self):
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_entry(self, entry):
        self.clear_right_panel()

        test = entry.test_name.lower()

        if "keyboard" in test:
            view = KeyboardMultiTestView(entry)
        elif "gamepad" in test:
            view = GamepadMultiTestView(entry)
        elif "mouse" in test:
            view = MouseMultiTestView(entry)
        elif "audioinput" in test:
            view = AudioInputTestView(entry)
        elif "storagesinglefile" in test:
            view = StorageSingleFileTestView(entry)
        elif "storagemultifile" in test:
            view = StorageMultiFileTestView(entry)
        else:
            view = QLabel("Unsupported test type")
            view.setAlignment(Qt.AlignCenter)
            view.setStyleSheet("color: #888;")

        self.right_layout.addWidget(view)

