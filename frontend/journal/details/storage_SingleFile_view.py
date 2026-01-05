from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from frontend.utils.utility_functions import clean_serial, shorten_pnp_id


def bytes_to_gb(value: int) -> float:
    return round(value / (1024 ** 3), 2)


class StorageSingleFileTestView(QWidget):
    def __init__(self, entry, parent=None):
        super().__init__(parent)

        raw = entry.raw
        device = raw.get("device", {})
        drive = raw.get("drive", {})
        result = raw.get("result", {})

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # ============================
        # HEADER
        # ============================
        title = QLabel(
            device.get("model", "Storage Device")
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
        device_frame = QFrame()
        device_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 6px;
            }
        """)

        device_layout = QVBoxLayout(device_frame)
        device_layout.setContentsMargins(12, 10, 12, 10)
        device_layout.setSpacing(6)

        def info(label, value):
            l = QLabel(f"{label}: <b>{value}</b>")
            l.setStyleSheet("color: #cccccc;")
            return l

        serial = clean_serial(device.get("serial"))
        pnp_full = device.get("pnp_id")
        pnp_short = shorten_pnp_id(pnp_full)

        lbl_pnp = info("PNP ID", pnp_short)
        lbl_pnp.setToolTip(pnp_full)

        device_layout.addWidget(info("Interface", device.get("interface", "—")))
        device_layout.addWidget(info("Bus", device.get("bus", "—")))
        device_layout.addWidget(lbl_pnp)
        device_layout.addWidget(info("Serial", serial))

        layout.addWidget(device_frame)

        # ============================
        # DRIVE INFO PANEL
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

        total_bytes = drive.get("total_bytes")
        free_bytes = drive.get("free_bytes")

        if isinstance(total_bytes, int) and isinstance(free_bytes, int):
            total_gb = bytes_to_gb(total_bytes)
            free_gb = bytes_to_gb(free_bytes)
            free_pct = round((free_bytes / total_bytes) * 100, 1)
            capacity_str = (
                f"{total_gb} GB "
                f"(Free: {free_gb} GB / {free_pct}%)"
            )
        else:
            capacity_str = "—"

        drive_layout.addWidget(info(
            "Drive path [At test]", drive.get("path", "—")
        ))
        drive_layout.addWidget(info(
            "Filesystem", drive.get("filesystem", "—")
        ))
        drive_layout.addWidget(info(
            "Capacity", capacity_str
        ))

        layout.addWidget(drive_frame)

        # ============================
        # RESULT PANEL
        # ============================
        result_frame = QFrame()
        result_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 6px;
            }
        """)

        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(12, 10, 12, 10)
        result_layout.setSpacing(6)

        result_layout.addWidget(info(
            "Read speed", f"{result.get('read_speed_MBps', '—')} MB/s"
        ))
        result_layout.addWidget(info(
            "Write speed", f"{result.get('write_speed_MBps', '—')} MB/s"
        ))
        result_layout.addWidget(info(
            "Data integrity",
            "PASS" if result.get("hash_match") else "FAIL"
        ))

        layout.addWidget(result_frame)

        layout.addStretch(1)
