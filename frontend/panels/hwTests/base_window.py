from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class BaseTestWindow(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setMinimumSize(800, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI Semibold", 20))
        title_lbl.setAlignment(Qt.AlignLeft)

        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setFont(QFont("Segoe UI", 11))
        subtitle_lbl.setStyleSheet("color: #9a9a9a;")

        placeholder = QLabel("🚧 Test UI placeholder\n\nBackend will be wired later")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                border: 2px dashed #333;
                border-radius: 8px;
                padding: 40px;
            }
        """)

        layout.addWidget(title_lbl)
        layout.addWidget(subtitle_lbl)
        #layout.addStretch(0.5)
        layout.addSpacing(8)
        # layout.addWidget(placeholder, 1)
