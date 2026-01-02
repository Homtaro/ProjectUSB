from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QFrame, QTextEdit, QListWidget,
)

from backend.modules.usbMonitoring import format_device_tree_full


class DevicePanel(QWidget):
    """Main USB device monitoring panel (locked layout)."""

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._build_ui()
        self.refresh_devices()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # ================= DETAILS TEXT AREA =================
        # self.details_text = QTextEdit()
        # self.details_text.setReadOnly(True)
        # main_layout.addWidget(self.details_text)

        # ================= TOP AREA =================
        top_layout = QHBoxLayout()
        top_layout.setSpacing(5)

        # ================= DEVICE TREE =================
        self.device_tree = QTreeWidget()
        # TODO: REWRITE INTO QLISTWIDGET
        #self.device_tree = QListWidget()
        self.device_tree.setHeaderLabel("USB Devices")
        self.device_tree.setFixedWidth(320)
        self.device_tree.setDragEnabled(False)

        self.device_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.device_tree.setTextElideMode(Qt.ElideNone)

        #TODO: CHANGE THIS LATER INTO AUTOMATIC HELPER FUNCTION
        self.device_tree.setColumnWidth(0, self.device_tree.width()+150)

        top_layout.addWidget(self.device_tree)

        # ================= INFO PANEL =================
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)

        # info_layout = QFormLayout(info_frame)
        # info_layout.setContentsMargins(15, 10, 15, 10)
        # info_layout.setLabelAlignment(Qt.AlignLeft)
        #
        # self.lbl_name = QLabel("—")
        # self.lbl_vid = QLabel("—")
        # self.lbl_pid = QLabel("—")
        # self.lbl_class = QLabel("—")
        # self.lbl_speed = QLabel("—")
        # self.lbl_power = QLabel("—")
        #
        # info_layout.addRow("Device Name:", self.lbl_name)
        # info_layout.addRow("VID:", self.lbl_vid)
        # info_layout.addRow("PID:", self.lbl_pid)
        # info_layout.addRow("Class:", self.lbl_class)
        # info_layout.addRow("Speed:", self.lbl_speed)
        # info_layout.addRow("Power:", self.lbl_power)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFontFamily("Consolas")
        self.details_text.setFontPointSize(9)
        self.details_text.setLineWrapMode(QTextEdit.NoWrap)

        top_layout.addWidget(self.details_text, 1)

        #top_layout.addWidget(info_frame, 1)

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

    def refresh_devices(self):
        self.device_tree.clear()

        devices = self.backend.get_usb_devices_full()

        root = QTreeWidgetItem(self.device_tree, ["USB Devices"])

        stats = {
            "total": 0,
            "hub": 0,
            "hid": 0,
            "audio": 0,
            "storage": 0,
            "video": 0
        }

        for dev in devices:
            stats["total"] += 1

            #name = dev["device_name"] or "Unknown Device"

            name_part1 = dev["device_name"]
            name_part2 = self.backend.resolve_device_name_format(dev)

            name = f"{name_part1} ({name_part2})"

            vid = dev["vid"]
            pid = dev["pid"]

            item = QTreeWidgetItem(root, [name])
            item.setToolTip(0, name)
            item.setData(0, Qt.UserRole, dev)

            class_name = dev["class_name"]

            #TODO: REFACTOR THIS INTO BACKEND LATER

            found_types = set()

            for i in dev["interfaces"]:
                if i["class_name"] == "Human Interface Device":
                    if "hid" not in found_types:
                        stats["hid"] += 1
                        found_types.add("hid")

                elif i["class_name"] == "Mass Storage":
                    if "storage" not in found_types:
                        stats["storage"] += 1
                        found_types.add("storage")

                elif i["class_name"] == "Hub":
                    if "hub" not in found_types:
                        stats["hub"] += 1
                        found_types.add("hub")

                elif i["class_name"] == "Video":
                    if "video" not in found_types:
                        stats["video"] += 1
                        found_types.add("video")

                elif i["class_name"] == "Audio":
                    if "audio" not in found_types:
                        stats["audio"] += 1
                        found_types.add("audio")

            # if "Hub" in class_name:
            #     stats["hub"] += 1
            # if "Human Interface" in class_name:
            #     stats["hid"] += 1
            # if "Audio" in class_name:
            #     stats["audio"] += 1
            # if "Mass Storage" in class_name:
            #     stats["storage"] += 1

        self.device_tree.expandAll()

        self.lbl_total.setText(f"Devices: {stats['total']}")
        self.lbl_hubs.setText(f"Hubs: {stats['hub']}")
        self.lbl_hid.setText(f"HID: {stats['hid']}")
        self.lbl_audio.setText(f"Audio: {stats['audio']}")
        self.lbl_storage.setText(f"Storage: {stats['storage']}")

    # def _on_device_selected(self, item, _):
    #     if not item:
    #         return
    #
    #     dev = item.data(0, Qt.UserRole)
    #     if not dev:
    #         return
    #
    #     self.lbl_name.setText(dev["device_name"] or "—")
    #     self.lbl_vid.setText(dev["vid"])
    #     self.lbl_pid.setText(dev["pid"])
    #     self.lbl_class.setText(dev["class_name"])
    #
    #     power = dev.get("power", {})
    #     self.lbl_power.setText(
    #         f'{power.get("max_power_ma", "—")} mA'
    #     )
    #
    #     self.lbl_speed.setText("—")  # optional later

    # def _on_device_selected(self, item, _):
    #     dev_info = item.data(0, Qt.UserRole)
    #     if not dev_info:
    #         return
    #
    #     text = format_device_tree_full(dev_info)
    #     self.details_text.setPlainText(text)

    def _on_device_selected(self, item, _):
        if not item:
            return

        info = item.data(0, Qt.UserRole)
        if not info:
            return

        text = format_device_tree_full(info)
        self.details_text.setPlainText(text)
