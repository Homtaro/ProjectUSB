from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class AudioInputTestView(QWidget):
    def __init__(self, entry, parent=None):
        super().__init__(parent)

        raw = entry.raw
        device = raw.get("device", {})
        result = raw.get("result", {})

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # ============================
        # HEADER
        # ============================
        title = QLabel(
            device.get("name", "Audio Input Device")
        )
        title.setFont(QFont("Segoe UI Semibold", 16))
        title.setStyleSheet("color: #ffffff;")

        subtitle = QLabel(
            f"{entry.test_name} • {entry.date}"
        )
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #aaaaaa;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ============================
        # DEVICE INFO PANEL
        # ============================
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 6px;
            }
        """)

        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(6)

        def info(label, value):
            l = QLabel(f"{label}: <b>{value}</b>")
            l.setStyleSheet("color: #cccccc;")
            return l

        info_layout.addWidget(info(
            "Bus", device.get("bus", "—")
        ))
        info_layout.addWidget(info(
            "PNP ID", device.get("pnp_id", "—")
        ))

        layout.addWidget(info_frame)

        # ============================
        # RESULT / STATS PANEL
        # ============================
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 6px;
            }
        """)

        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(12, 10, 12, 10)
        stats_layout.setSpacing(6)

        stats_layout.addWidget(info(
            "Signal detected",
            "YES" if result.get("signal") else "NO"
        ))
        stats_layout.addWidget(info(
            "Peak level",
            f"{result.get('peak', '—'):.4f}"
            if isinstance(result.get("peak"), (int, float)) else "—"
        ))
        stats_layout.addWidget(info(
            "RMS level",
            f"{result.get('rms', '—'):.4f}"
            if isinstance(result.get("rms"), (int, float)) else "—"
        ))

        layout.addWidget(stats_frame)

        layout.addStretch(1)
