from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.modules.scanCodeConvert import scancode_to_key


class KeyboardMultiTestView(QWidget):
    def __init__(self, entry, parent=None):
        super().__init__(parent)

        raw = entry.raw
        device = raw.get("device", {})
        stats = raw.get("stats", {})
        heatmap = raw.get("heatmap", {})

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # ============================
        # HEADER
        # ============================
        title = QLabel(
            f"{device.get('decoded_name', 'Keyboard')} "
            f"[{entry.pid_vid}]"
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
        # STATS PANEL
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

        def stat(label, value):
            l = QLabel(f"{label}: <b>{value}</b>")
            l.setStyleSheet("color: #cccccc;")
            return l

        stats_layout.addWidget(stat("Total presses", stats.get("total_presses", "—")))
        stats_layout.addWidget(stat("Unique keys", stats.get("unique_keys", "—")))
        stats_layout.addWidget(stat("Max simultaneous", stats.get("max_simultaneous", "—")))
        stats_layout.addWidget(
            stat("NKRO supported", "YES" if stats.get("nkro_supported") else "NO")
        )

        layout.addWidget(stats_frame)

        # ============================
        # HEATMAP TABLE
        # ============================
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels([
            "Key",
            "Scancode",
            "Presses"
        ])

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setAlternatingRowColors(True)

        # ---- Sort heatmap ----
        rows = []
        for sc_str, count in heatmap.items():
            sc = int(sc_str)
            rows.append((sc, count))

        rows.sort(key=lambda x: x[1], reverse=True)

        table.setRowCount(len(rows))

        for r, (scancode, count) in enumerate(rows):
            key_name = scancode_to_key(scancode)

            table.setItem(r, 0, QTableWidgetItem(key_name))
            table.setItem(r, 1, QTableWidgetItem(f"0x{scancode:X}"))
            table.setItem(r, 2, QTableWidgetItem(str(count)))

        layout.addWidget(table, 1)
