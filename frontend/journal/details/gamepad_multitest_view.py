from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class GamepadMultiTestView(QWidget):
    def __init__(self, entry, parent=None):
        super().__init__(parent)

        raw = entry.raw
        device = raw.get("device", {})
        stats = raw.get("stats", {})
        heatmap = raw.get("button_heatmap", {})

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # ============================
        # HEADER
        # ============================
        device_name = (
            device.get("decoded_name")
            or device.get("name")
            or "Gamepad"
        )

        title = QLabel(
            f"{device_name} [{entry.pid_vid}]"
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
        # DEVICE META
        # ============================
        serial = device.get("serial")
        if serial:
            serial_lbl = QLabel(f"Serial: <b>{serial}</b>")
            serial_lbl.setStyleSheet("color: #cccccc;")
            layout.addWidget(serial_lbl)

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

        stats_layout.addWidget(
            stat("Polling rate", f"{stats.get('polling_rate_hz', '—')} Hz")
        )

        # ---- Stick stats ----
        for stick_name in ("left_stick", "right_stick"):
            stick = stats.get(stick_name)
            if not stick:
                continue

            stats_layout.addWidget(QLabel(
                f"<b>{stick_name.replace('_', ' ').title()}</b>"
            ))

            stats_layout.addWidget(
                stat("Max radius", stick.get("max_radius", "—"))
            )
            stats_layout.addWidget(
                stat("Mean radius", stick.get("mean_radius", "—"))
            )
            stats_layout.addWidget(
                stat(
                    "Circular error",
                    f"{stick.get('circular_error', '—')} "
                    f"({stick.get('circular_error_pct', '—')}%)"
                )
            )

        layout.addWidget(stats_frame)

        # ============================
        # BUTTON HEATMAP TABLE
        # ============================
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([
            "Button",
            "Presses"
        ])

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setAlternatingRowColors(True)

        # ---- Sort by presses desc ----
        rows = sorted(
            heatmap.items(),
            key=lambda x: x[1],
            reverse=True
        )

        table.setRowCount(len(rows))

        for r, (button, count) in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(button))
            table.setItem(r, 1, QTableWidgetItem(str(count)))

        layout.addWidget(table, 1)
