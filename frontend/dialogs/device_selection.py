
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel, QHBoxLayout
)

class DeviceSelectionDialog(QDialog):
    def __init__(self, devices: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select keyboard to test")
        self.setModal(True)
        self.resize(450, 300)

        self.selected_device = None

        layout = QVBoxLayout(self)

        label = QLabel("Select keyboard device:")
        layout.addWidget(label)

        self.list = QListWidget()
        layout.addWidget(self.list)

        for dev in devices:
            text = f"{dev['name']}  [{dev['vid']:04X}:{dev['pid']:04X}]"
            self.list.addItem(text)

        btns = QHBoxLayout()
        ok = QPushButton("Start test")
        cancel = QPushButton("Cancel")
        btns.addStretch(1)
        btns.addWidget(ok)
        btns.addWidget(cancel)

        layout.addLayout(btns)

        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

    def accept(self):
        row = self.list.currentRow()
        if row < 0:
            return
        self.selected_device = row
        super().accept()
