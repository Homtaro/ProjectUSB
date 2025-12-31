from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QListWidget, QListWidgetItem,
    QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from frontend.style.theme import *


ACCENT_COLOR = "#0078d7"


# --------------------------------
# Single journal entry widget
# --------------------------------
class JournalEntryItem(QFrame):
    def __init__(
        self,
        date: str,
        category: str,
        pid_vid: str,
        device_name: str,
        test_name: str,
        parent=None
    ):
        super().__init__(parent)

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(88)

        # Hover applies ONLY to the whole entry
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
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        top = QLabel(f"{date} • {category}")
        top.setFont(QFont("Segoe UI", 9))
        top.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_MUTED};
            }}
        """)

        name = QLabel(device_name)
        name.setFont(QFont("Segoe UI Semibold", 10))
        name.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
            }}
        """)

        meta = QLabel(f"{test_name}   |   {pid_vid}")
        meta.setFont(QFont("Segoe UI", 9))
        meta.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
            }}
        """)

        layout.addWidget(top)
        layout.addWidget(name)
        layout.addWidget(meta)



# --------------------------------
# Journal panel
# --------------------------------
class JournalPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ============================
        # LEFT SIDE — JOURNAL LIST
        # ============================
        left_panel = QFrame()
        left_panel.setFixedWidth(380)
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #1b1b1b;
                border-right: 1px solid #2a2a2a;
            }
        """)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        title = QLabel("Test Journal")
        title.setFont(QFont("Segoe UI Semibold", 18))
        title.setStyleSheet("color: #ffffff;")

        # ---- Search bar
        search = QLineEdit()
        search.setPlaceholderText("Search device, test, PID/VID...")
        search.setFixedHeight(34)
        search.setStyleSheet("""
            QLineEdit {
                background-color: #222;
                border: 1px solid #2d2d2d;
                border-radius: 6px;
                padding: 6px 8px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
        """)

        # ---- Filters row
        filters = QHBoxLayout()
        filters.setSpacing(8)

        sort_box = QComboBox()
        sort_box.addItems(["Newest first", "Oldest first"])
        sort_box.setFixedHeight(30)

        category_box = QComboBox()
        category_box.addItems([
            "All categories",
            "Keyboard",
            "Mouse",
            "Gamepad",
            "Audio",
            "Storage"
        ])
        category_box.setFixedHeight(30)

        test_box = QComboBox()
        test_box.addItems([
            "All tests",
            "Multitest",
            "Playback Test",
            "Microphone Test",
            "Storage Test"
        ])
        test_box.setFixedHeight(30)

        for box in (sort_box, category_box, test_box):
            box.setStyleSheet("""
                QComboBox {
                    background-color: #222;
                    border: 1px solid #2d2d2d;
                    border-radius: 6px;
                    padding: 4px 6px;
                    color: #ffffff;
                }
            """)

        filters.addWidget(sort_box)
        filters.addWidget(category_box)
        filters.addWidget(test_box)

        # ---- Journal list
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

        journal_container = QWidget()
        journal_layout = QVBoxLayout(journal_container)
        journal_layout.setSpacing(10)
        journal_layout.setContentsMargins(0, 0, 0, 0)
        journal_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(journal_container)

        # Dummy entries (for layout testing)
        for i in range(8):
            journal_layout.addWidget(
                JournalEntryItem(
                    date="2025-03-12",
                    category="Mouse",
                    pid_vid="046D:C534",
                    device_name="Logitech G403",
                    test_name="Multitest"
                )
            )

        journal_layout.addStretch(1)

        left_layout.addWidget(title)
        left_layout.addWidget(search)
        left_layout.addLayout(filters)
        left_layout.addWidget(scroll, 1)

        # ============================
        # RIGHT SIDE — DETAILS
        # ============================
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: transparent;")

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(32, 24, 32, 24)
        right_layout.setSpacing(16)

        header = QLabel("Test Result")
        header.setFont(QFont("Segoe UI Semibold", 22))
        header.setStyleSheet("color: #ffffff;")

        sub = QLabel("Select an entry to view detailed results")
        sub.setFont(QFont("Segoe UI", 11))
        sub.setStyleSheet("color: #9a9a9a;")

        placeholder = QLabel("No test selected")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setFont(QFont("Segoe UI", 14))
        placeholder.setStyleSheet("color: #555555;")

        right_layout.addWidget(header)
        right_layout.addWidget(sub)
        right_layout.addStretch(1)
        right_layout.addWidget(placeholder)
        right_layout.addStretch(2)

        # ============================
        # ASSEMBLY
        # ============================
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
