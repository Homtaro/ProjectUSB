from PySide6.QtCore import QThread, QEvent
from PySide6.QtWidgets import (
    QListWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout
)

from frontend.panels.hwTests.base_window import BaseTestWindow


class AudioOutputTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Audio Playback Test",
            subtitle="Left / right channel diagnostics",
            parent=parent
        )

        self.setStyleSheet("""
                                QPushButton:disabled {
                                    border: 2px solid #a33;
                                    color: #777;
                                    background-color: #1a1a1a;
                                }
                                """)

        self.setFixedSize(900, 500)

        self.thread = None
        self.worker = None

        # ================= ROOT =================
        root = QHBoxLayout()
        root.setSpacing(16)

        # ==================================================
        # LEFT: DEVICE LIST
        # ==================================================
        left = QVBoxLayout()
        left.setSpacing(8)

        lbl_devices = QLabel("Output devices (WASAPI)")
        lbl_devices.setStyleSheet("font-weight: bold;")

        self.device_list = QListWidget()
        self.device_list.setMinimumWidth(350)

        self.btn_refresh = QPushButton("Refresh devices")
        self.btn_refresh.setFixedHeight(26)

        left.addWidget(lbl_devices)
        left.addWidget(self.device_list, 1)
        left.addWidget(self.btn_refresh)

        # ==================================================
        # RIGHT: CONTROLS
        # ==================================================
        right = QVBoxLayout()
        right.setSpacing(8)

        lbl_controls = QLabel("Controls")
        lbl_controls.setStyleSheet("font-weight: bold;")

        self.btn_left = QPushButton("Left channel (440 Hz)")
        self.btn_right = QPushButton("Right channel (440 Hz)")
        self.btn_sweep = QPushButton("Stereo sweep (L → R)")

        for btn in (self.btn_left, self.btn_right, self.btn_sweep):
            btn.setFixedHeight(28)

        info = QLabel(
            "⚠ Volume limited to safe level\n"
            "Listen for correct channel routing"
        )
        info.setStyleSheet("color: #aaaaaa;")

        right.addWidget(lbl_controls)
        right.addWidget(self.btn_left)
        right.addWidget(self.btn_right)
        right.addWidget(self.btn_sweep)
        right.addSpacing(6)
        right.addWidget(info)
        right.addStretch(1)

        # ================= FINAL =================
        root.addLayout(left, 1)
        root.addLayout(right, 1)
        self.layout().addLayout(root)

        # ================= SIGNALS =================
        self.btn_refresh.clicked.connect(self.refresh_devices)
        self.btn_left.clicked.connect(lambda: self.run_test("left"))
        self.btn_right.clicked.connect(lambda: self.run_test("right"))
        self.btn_sweep.clicked.connect(lambda: self.run_test("sweep"))

        self.refresh_devices()

    # ==================================================
    # DEVICE MANAGEMENT
    # ==================================================

    def refresh_devices(self):
        self.device_list.clear()
        for idx, name in self.backend.list_audio_output_devices():
            self.device_list.addItem(f"{idx}: {name}")

    # ==================================================
    # TEST EXECUTION
    # ==================================================

    def run_test(self, mode: str):
        if not self.device_list.currentItem():
            return

        idx = int(self.device_list.currentItem().text().split(":")[0])

        self._set_controls(False)

        self.thread = QThread(self)
        self.worker = self.backend.create_audio_output_test(idx)
        self.worker.moveToThread(self.thread)

        if mode == "left":
            self.thread.started.connect(self.worker.left_test)
        elif mode == "right":
            self.thread.started.connect(self.worker.right_test)
        else:
            self.thread.started.connect(self.worker.sweep)


        self.worker.finished.connect(self.thread.quit)

        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.error.connect(self.on_error)

        self.thread.finished.connect(lambda: self._set_controls(True))

        self.thread.start()

    def _set_controls(self, enabled: bool):
        print("Controls:", enabled)
        for btn in (self.btn_left, self.btn_right, self.btn_sweep, self.btn_refresh):
            btn.setEnabled(enabled)

    def on_error(self, msg):
        print("Audio output error:", msg)
        if self.thread:
            self.thread.quit()

    def event(self, e):
        if e.type() == QEvent.Close:
            self._set_controls(False)

            try:
                if self.thread:
                    self.thread.quit()
                    self.thread.wait(1000)
            except RuntimeError:
                pass

            self.thread = None
            self.worker = None
            e.accept()
            return True

        return super().event(e)


