from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from frontend.graphs.base_graph import TimeSeriesGraph


class MouseMultiTestView(QWidget):
    def __init__(self, entry, parent=None):
        super().__init__(parent)

        raw = entry.raw
        device = raw.get("device", {})
        stats = raw.get("stats", {})
        config = raw.get("config", {})
        graphs = raw.get("graphs", {})
        heatmap = raw.get("button_heatmap", {})

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # ============================
        # HEADER
        # ============================
        title = QLabel(
            f"{device.get('decoded_name', 'Mouse')} "
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
        # CONFIG PANEL
        # ============================
        # config_frame = QFrame()
        # config_frame.setStyleSheet("""
        #     QFrame {
        #         background-color: #1e1e1e;
        #         border-radius: 6px;
        #     }
        # """)
        #
        # config_layout = QVBoxLayout(config_frame)
        # config_layout.setContentsMargins(12, 10, 12, 10)
        # config_layout.setSpacing(6)
        #
        # def cfg(label, value):
        #     l = QLabel(f"{label}: <b>{value}</b>")
        #     l.setStyleSheet("color: #cccccc;")
        #     return l
        #
        # config_layout.addWidget(cfg(
        #     "Duration", f"{config.get('duration_sec', '—')} s"
        # ))
        # config_layout.addWidget(cfg(
        #     "Polling window", f"{config.get('polling_window_ms', '—')} ms"
        # ))
        # config_layout.addWidget(cfg(
        #     "Jitter bucket", f"{config.get('jitter_bucket_ms', '—')} ms"
        # ))
        #
        # layout.addWidget(config_frame)

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

        stats_layout.addWidget(stat(
            "Polling rate", f"{stats.get('polling_rate_hz', '—')} Hz"
        ))
        stats_layout.addWidget(stat(
            "Average jitter", f"{stats.get('avg_jitter_ms', '—')} ms"
        ))
        stats_layout.addWidget(stat(
            "Packets captured", stats.get("packet_count", "—")
        ))

        layout.addWidget(stats_frame)

        # ============================
        # GRAPHS
        # ============================
        polling_graph = TimeSeriesGraph("Polling Rate", "Hz")
        polling_graph.set_data(graphs.get("polling_rate", []))

        jitter_graph = TimeSeriesGraph("Jitter", "ms")
        jitter_graph.set_data(graphs.get("jitter", []))

        polling_graph.setMinimumHeight(60)
        polling_graph.setMaximumHeight(100)

        jitter_graph.setMinimumHeight(60)
        jitter_graph.setMaximumHeight(100)

        layout.addWidget(polling_graph, 1)
        layout.addWidget(jitter_graph, 1)

        # ============================
        # BUTTON HEATMAP TABLE
        # ============================
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([
            "Button",
            "Presses"
        ])

        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )

        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setAlternatingRowColors(True)

        rows = sorted(
            heatmap.items(),
            key=lambda x: x[1],
            reverse=True
        )

        table.setRowCount(len(rows))

        for r, (btn, count) in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(btn))
            table.setItem(r, 1, QTableWidgetItem(str(count)))

        layout.addWidget(table, 1)
