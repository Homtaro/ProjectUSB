from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

import string


# ============================
# helpers (same as single-file)
# ============================
def clean_serial(value):
    if not value or not isinstance(value, str):
        return "—"
    cleaned = "".join(c for c in value if c in string.printable).strip()
    if len(cleaned) < 4 or cleaned.count("0") == len(cleaned):
        return "Unavailable"
    return cleaned


def shorten_pnp_id(pnp, max_len=48):
    if not pnp:
        return "—"
    return pnp if len(pnp) <= max_len else pnp[:max_len - 1] + "…"


def bytes_to_gb(value):
    return value / (1024 ** 3)


# ============================
# VIEW
# ============================
class StorageMultiFileTestView(QWidget):
    def __init__(self, entry, parent=None):
        super().__init__(parent)

        raw = entry.raw
        device = raw.get("device", {})
        drive = raw.get("drive", {})
        files = raw.get("files", [])
        summary = raw.get("summary", {})

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        # ============================
        # HEADER
        # ============================
        title = QLabel(device.get("model", "Storage Device"))
        title.setFont(QFont("Segoe UI Semibold", 18))
        title.setStyleSheet("color: #ffffff;")

        subtitle = QLabel(f"{entry.test_name} • {entry.date}")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #aaaaaa;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ============================
        # DEVICE INFO
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

        serial = clean_serial(device.get("serial"))
        pnp_full = device.get("pnp_id")
        pnp_short = shorten_pnp_id(pnp_full)

        lbl_pnp = info("PNP ID", pnp_short)
        lbl_pnp.setToolTip(pnp_full)

        info_layout.addWidget(info("Interface", device.get("interface", "—")))
        info_layout.addWidget(info("Bus", device.get("bus", "—")))
        info_layout.addWidget(lbl_pnp)
        info_layout.addWidget(info("Serial", serial))

        layout.addWidget(info_frame)

        # ============================
        # DRIVE INFO
        # ============================
        drive_frame = QFrame()
        drive_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 6px;
            }
        """)

        drive_layout = QVBoxLayout(drive_frame)
        drive_layout.setContentsMargins(12, 10, 12, 10)
        drive_layout.setSpacing(6)

        total = drive.get("total_bytes", 0)
        free = drive.get("free_bytes", 0)

        total_gb = bytes_to_gb(total)
        free_gb = bytes_to_gb(free)
        free_pct = (free / total * 100) if total else 0

        drive_layout.addWidget(info("Path", drive.get("path", "—")))
        drive_layout.addWidget(info("Filesystem", drive.get("filesystem", "—")))
        drive_layout.addWidget(
            info(
                "Capacity",
                f"{total_gb:.1f} GB (free {free_gb:.1f} GB / {free_pct:.1f}%)"
            )
        )

        layout.addWidget(drive_frame)

        # ============================
        # SUMMARY
        # ============================
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 6px;
            }
        """)

        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(12, 10, 12, 10)
        summary_layout.setSpacing(6)

        summary_layout.addWidget(
            info("Avg read speed", f"{summary.get('avg_read_MBps', '—')} MB/s")
        )
        summary_layout.addWidget(
            info("Avg write speed", f"{summary.get('avg_write_MBps', '—')} MB/s")
        )
        summary_layout.addWidget(
            info(
                "Files verified",
                f"{summary.get('files_ok', 0)} / {summary.get('files_total', 0)}"
            )
        )

        layout.addWidget(summary_frame)

        # ============================
        # FILE RESULTS TABLE
        # ============================
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels([
            "File",
            "Read MB/s",
            "Write MB/s",
            "Integrity"
        ])

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setAlternatingRowColors(True)

        table.setRowCount(len(files))

        for r, f in enumerate(files):
            table.setItem(r, 0, QTableWidgetItem(f.get("file", "—")))
            table.setItem(r, 1, QTableWidgetItem(str(f.get("read_MBps", "—"))))
            table.setItem(r, 2, QTableWidgetItem(str(f.get("write_MBps", "—"))))

            ok = f.get("hash_match")
            integrity = "OK" if ok else "FAIL"
            cell = QTableWidgetItem(integrity)
            cell.setForeground(Qt.green if ok else Qt.red)
            table.setItem(r, 3, cell)

        layout.addWidget(table, 1)
