# frontend/panels/hwTests/mouse/multiTestMouse.py

from PySide6.QtCore import Qt, QThread, QTimer, QEvent
from PySide6.QtWidgets import (
    QPushButton, QHBoxLayout, QVBoxLayout,
    QListWidget, QLabel, QFrame, QDialog
)

from frontend.dialogs.device_selection import DeviceSelectionDialog
from frontend.panels.hwTests.base_window import BaseTestWindow
from frontend.panels.hwTests.mouse.mouse_visual import MouseVisualPanel


class MouseMultiTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Mouse Multitest",
            subtitle="Heatmap, polling rate, jitter",
            parent=parent
        )

        # ================= Variable =================

        self.setVisible(False)

        self.thread: QThread | None = None
        self.worker = None
        self._final_result = None

        self.selected_vid = None
        self.selected_pid = None

        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(33)  # ~30 FPS
        self.ui_timer.timeout.connect(self.refresh_ui)
        self.ui_timer.start()




        self.setFixedSize(1200, 700)

        # ================= TOP AREA =================

        top = QHBoxLayout()

        # ---- Left: Mouse heatmap ----
        self.mouse_panel = MouseVisualPanel(self)
        top.addWidget(self.mouse_panel, 0, Qt.AlignTop)

        # ---- Right: Charts / movement placeholder ----
        right = QVBoxLayout()

        self.lbl_polling = QLabel("Polling rate: — Hz")
        self.lbl_jitter = QLabel("Average jitter: —")

        for lbl in (self.lbl_polling, self.lbl_jitter):
            lbl.setStyleSheet("color: #e0e0e0; font-size: 14px;")

        chart_placeholder = QLabel("📈 Charts will appear here")
        chart_placeholder.setAlignment(Qt.AlignCenter)
        chart_placeholder.setStyleSheet("""
            QLabel {
                border: 2px dashed #333;
                border-radius: 8px;
                color: #888;
                padding: 40px;
            }
        """)

        #right.addWidget(self.lbl_polling)
        #right.addWidget(self.lbl_jitter)
        right.addSpacing(12)
        right.addWidget(chart_placeholder, 1)

        top.addLayout(right, 1)

        # ================= BOTTOM AREA =================

        bottom = QHBoxLayout()

        self.history = QListWidget()
        self.history.setMinimumWidth(350)
        self.history.setFrameShape(QFrame.StyledPanel)

        controls = QVBoxLayout()

        self.btn_start = QPushButton("Start test (10s)")
        self.btn_start.setFixedHeight(40)

        controls.addWidget(self.btn_start)
        controls.addWidget(self.lbl_polling)
        controls.addWidget(self.lbl_jitter)
        controls.addStretch(1)

        bottom.addWidget(self.history, 2)
        bottom.addLayout(controls, 1)

        # ================= FINAL LAYOUT =================

        container = QVBoxLayout()
        container.setSpacing(16)
        container.addLayout(top, 2)
        container.addLayout(bottom, 1)

        self.layout().addLayout(container)

        # ================= STATE =================

        self.btn_start.clicked.connect(self._on_start_clicked)


        # ================== RUNNING =================

        QTimer.singleShot(0, self.select_device_and_start)


    # ================= DEVICE SELECTION =================


    def select_device_and_start(self):
        devices = self.backend.get_hid_mouse()

        if not devices:
            print("No HID mice found")
            self.close()
            return

        dlg = DeviceSelectionDialog(devices, self)
        if dlg.exec() != QDialog.Accepted:
            self.close()
            return

        dev = devices[dlg.selected_device]
        self.selected_vid = dev["vid"]
        self.selected_pid = dev["pid"]

        self.show()

    # ================= PLACEHOLDERS =================

    def _on_start_clicked(self):
        if self.worker:
            return

        self.history.clear()
        self.mouse_panel.reset()

        self.lbl_polling = QLabel("Polling rate: — Hz")
        self.lbl_jitter = QLabel("Average jitter: —")

        self.btn_start.setEnabled(False)
        self.log_event("▶ Test started")



        self.start_test()

    # === API for backend (later) ===

    def start_test(self):
        if self.selected_vid is None or self.selected_pid is None:
            return

        self.thread = QThread(self)
        self.worker = self.backend.create_mouse_test(
            vid=self.selected_vid,
            pid=self.selected_pid,
            duration=10
        )

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_test_finished)
        self.worker.finished.connect(self.thread.quit)

        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def refresh_ui(self):
        if not self.worker:
            return

        for event in self.worker.pop_events(100):
            etype = event[0]

            if etype == "button":
                name = event[1]
                self.mouse_panel.button_hit(name)
                self.log_event(f"BUTTON {name}")

            elif etype == "wheel":
                direction = event[1]
                self.mouse_panel.button_hit(f"wheel_{direction}")
                self.log_event(f"WHEEL {direction}")

            elif etype == "move":
                # dx, dy, magnitude (we don’t draw path yet)
                pass

            elif etype == "start":
                self.log_event("▶ Capture started")

            elif etype == "end":
                self.log_event("■ Capture finished")

    def on_test_finished(self, result):
        self._final_result = result

        stats = result["stats"]
        self.update_stats(
            stats["polling_rate_hz"],
            stats["avg_jitter"]
        )

        self.log_event("✔ Test finished")

        self.btn_start.setEnabled(True)

        self.worker = None
        self.thread = None

    def event(self, e):
        if e.type() == QEvent.Close:
            if self.worker:
                self.worker.stop()
            if self.thread:
                self.thread.quit()
                self.thread.wait()

            self.worker = None
            self.thread = None

            e.accept()
        return super().event(e)

    def log_event(self, text: str):
        self.history.addItem(text)
        self.history.scrollToBottom()

    def update_stats(self, polling: int, jitter: float):
        self.lbl_polling.setText(f"Polling rate: {polling} Hz")
        self.lbl_jitter.setText(f"Average jitter: {jitter}")

    def reset_ui(self):
        self.mouse_panel.reset()
        self.history.clear()
        self.btn_start.setEnabled(True)
