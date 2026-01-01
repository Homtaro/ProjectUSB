from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)


class DevicePanel(QWidget):
    """Main USB device monitoring panel (locked layout)."""

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._build_ui()
        self._populate_dummy_data()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # ================= TOP AREA =================
        top_layout = QHBoxLayout()
        top_layout.setSpacing(5)

        # ================= DEVICE TREE =================
        self.device_tree = QTreeWidget()
        self.device_tree.setHeaderLabel("USB Devices")
        self.device_tree.setFixedWidth(320)
        self.device_tree.setDragEnabled(False)

        top_layout.addWidget(self.device_tree)

        # ================= INFO PANEL =================
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)

        info_layout = QFormLayout(info_frame)
        info_layout.setContentsMargins(15, 10, 15, 10)
        info_layout.setLabelAlignment(Qt.AlignLeft)

        self.lbl_name = QLabel("—")
        self.lbl_vid = QLabel("—")
        self.lbl_pid = QLabel("—")
        self.lbl_class = QLabel("—")
        self.lbl_speed = QLabel("—")
        self.lbl_power = QLabel("—")

        info_layout.addRow("Device Name:", self.lbl_name)
        info_layout.addRow("VID:", self.lbl_vid)
        info_layout.addRow("PID:", self.lbl_pid)
        info_layout.addRow("Class:", self.lbl_class)
        info_layout.addRow("Speed:", self.lbl_speed)
        info_layout.addRow("Power:", self.lbl_power)

        top_layout.addWidget(info_frame, 1)

        main_layout.addLayout(top_layout, 1)

        # ================= STATS BAR =================
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_frame.setFixedHeight(45)

        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(10, 5, 10, 5)
        stats_layout.setSpacing(20)

        self.lbl_total = QLabel("Devices: 0")
        self.lbl_hubs = QLabel("Hubs: 0")
        self.lbl_hid = QLabel("HID: 0")
        self.lbl_audio = QLabel("Audio: 0")
        self.lbl_storage = QLabel("Storage: 0")

        for lbl in (
            self.lbl_total,
            self.lbl_hubs,
            self.lbl_hid,
            self.lbl_audio,
            self.lbl_storage,
        ):
            lbl.setAlignment(Qt.AlignVCenter)
            stats_layout.addWidget(lbl)

        stats_layout.addStretch()

        main_layout.addWidget(stats_frame)

        # ================= SIGNALS =================
        self.device_tree.currentItemChanged.connect(self._on_device_selected)

    def _populate_dummy_data(self):
        root = QTreeWidgetItem(self.device_tree, ["USB Root Hub"])
        hub1 = QTreeWidgetItem(root, ["Generic USB Hub"])
        QTreeWidgetItem(hub1, ["USB Keyboard"])
        QTreeWidgetItem(hub1, ["USB Mouse"])

        hub2 = QTreeWidgetItem(root, ["External Hub"])
        QTreeWidgetItem(hub2, ["USB Flash Drive"])

        self.device_tree.expandAll()

        self.lbl_total.setText("Devices: 5")
        self.lbl_hubs.setText("Hubs: 2")
        self.lbl_hid.setText("HID: 2")
        self.lbl_audio.setText("Audio: 0")
        self.lbl_storage.setText("Storage: 1")

    def _on_device_selected(self, item, _):
        if not item:
            return

        self.lbl_name.setText(item.text(0))
        self.lbl_vid.setText("0x1234")
        self.lbl_pid.setText("0x5678")
        self.lbl_class.setText("HID")
        self.lbl_speed.setText("Full Speed")
        self.lbl_power.setText("100 mA")
