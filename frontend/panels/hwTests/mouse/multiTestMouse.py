# frontend/panels/hwTests/mouse/multiTestMouse.py

import json
import time

from PySide6.QtCore import Qt, QThread, QTimer, QEvent
from PySide6.QtWidgets import (
    QPushButton, QHBoxLayout, QVBoxLayout,
    QListWidget, QLabel, QFrame, QDialog,
    QProgressBar
)

from frontend.dialogs.device_selection import DeviceSelectionDialog
from frontend.graphs.base_graph import TimeSeriesGraph
from frontend.panels.hwTests.base_window import BaseTestWindow
from frontend.panels.hwTests.mouse.mouse_visual import MouseVisualPanel

#Raw Input controller (MAIN THREAD ONLY)
#from backend.modules.hwTests.mouse import mouseIsolated as rawmouse


class MouseMultiTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Mouse Multitest",
            subtitle="Heatmap, polling rate, jitter",
            parent=parent
        )

        # ================= CONFIG =================

        self.test_duration = 10  # seconds
        self.test_end_ts: float | None = None

        # ================= STATE =================

        self.setVisible(False)
        self.hide()

        self.thread: QThread | None = None
        self.worker = None
        self._final_result = None

        self.selected_vid = None
        self.selected_pid = None

        # ================= UI TIMER =================

        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(33)  # ~30 FPS
        self.ui_timer.timeout.connect(self.refresh_ui)
        self.ui_timer.start()

        # ================= WINDOW =================

        self.setFixedSize(1200, 700)

        self.setStyleSheet("""
        QPushButton {
            padding: 6px;
        }
        QPushButton:disabled {
            border: 2px solid #a33;
            color: #777;
            background-color: #1a1a1a;
        }
        QProgressBar {
            height: 18px;
            border-radius: 6px;
            background: #222;
        }
        QProgressBar::chunk {
            background: #3a8;
            border-radius: 6px;
        }
        """)

        # ================= TOP AREA =================

        top = QHBoxLayout()

        self.mouse_panel = MouseVisualPanel(self)
        top.addWidget(self.mouse_panel, 0, Qt.AlignTop)

        right = QVBoxLayout()

        self.lbl_timer = QLabel("Time left: —")
        self.lbl_timer.setStyleSheet(
            "color: #e0e0e0; font-size: 14px; font-weight: bold;"
        )

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.lbl_polling = QLabel("Polling rate: — Hz")
        self.lbl_jitter = QLabel("Average jitter: —")

        for lbl in (self.lbl_polling, self.lbl_jitter):
            lbl.setStyleSheet("color: #e0e0e0; font-size: 14px;")

        self.polling_graph = TimeSeriesGraph("Polling Rate", "Hz")
        self.jitter_graph = TimeSeriesGraph("Jitter", "ms")

        right.addWidget(self.lbl_timer)
        right.addWidget(self.progress)
        right.addSpacing(8)
        right.addWidget(self.polling_graph, 1)
        right.addWidget(self.jitter_graph, 1)

        top.addLayout(right, 1)

        # ================= BOTTOM AREA =================

        bottom = QHBoxLayout()

        self.history = QListWidget()
        self.history.setMinimumWidth(350)
        self.history.setFrameShape(QFrame.StyledPanel)

        controls = QVBoxLayout()

        self.btn_start = QPushButton(f"Start test ({self.test_duration}s)")
        self.btn_start.setFixedHeight(40)

        controls.addWidget(self.btn_start)
        controls.addSpacing(8)
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

        # ================= SIGNALS =================

        self.btn_start.clicked.connect(self._on_start_clicked)

        QTimer.singleShot(0, self.select_device_and_start)

    # ================= DEVICE SELECTION =================

    def select_device_and_start(self):
        devices = self.backend.get_hid_mouse()

        if not devices:
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

    # ================= RAW INPUT BRIDGE =================
    # MAIN THREAD → WORKER

    def on_raw_input_event(self, event_type, *data):
        if not self.worker:
            return
        self.worker.handle_event(event_type, *data)

    # ================= TEST START =================

    def _on_start_clicked(self):
        if self.worker:
            return

        self.history.clear()
        self.mouse_panel.reset()

        self.lbl_polling.setText("Polling rate: — Hz")
        self.lbl_jitter.setText("Average jitter: —")

        self.progress.setValue(0)
        self.test_end_ts = time.time() + self.test_duration

        self.btn_start.setEnabled(False)
        self.log_event("▶ Test started")

        self.start_test()

    def start_test(self):
        if self.selected_vid is None or self.selected_pid is None:
            return

        # --- worker thread (DATA ONLY) ---
        self.thread = QThread(self)
        self.worker = self.backend.create_mouse_test(
            vid=self.selected_vid,
            pid=self.selected_pid,
            duration=self.test_duration
        )
        self.worker.moveToThread(self.thread)

        self.worker.finished.connect(self.on_test_finished)
        self.worker.finished.connect(self.thread.quit)

        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        # --- RAW INPUT (MAIN THREAD) ---
        # rawmouse.start_capture(
        #     vid=self.selected_vid,
        #     pid=self.selected_pid,
        #     event_callback=self.on_raw_input_event,
        #     running_check=lambda: self.worker and self.worker._running
        # )

        self.backend.start_mouse_capture(
            vid=self.selected_vid,
            pid=self.selected_pid,
            event_callback=self.on_raw_input_event,
            running_check=lambda: self.worker and self.worker._running,
        )

        QTimer.singleShot(self.test_duration * 1000, self.stop_test)

    def stop_test(self):
        #rawmouse.stop_capture()
        self.backend.stop_mouse_capture()
        if self.worker:
            self.worker.finalize()

    # ================= UI UPDATE =================

    def refresh_ui(self):
        # --- timer & progress ---
        if self.test_end_ts:
            remaining = self.test_end_ts - time.time()
            if remaining <= 0:
                self.lbl_timer.setText("Time left: 0.0s")
                self.progress.setValue(100)
                self.test_end_ts = None
                self.log_event("Calculating results…")
            else:
                elapsed = self.test_duration - remaining
                percent = int((elapsed / self.test_duration) * 100)
                self.progress.setValue(min(percent, 100))
                self.lbl_timer.setText(f"Time left: {remaining:.1f}s")

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

    # ================= FINISH =================

    def on_test_finished(self, result):
        self._final_result = result

        stats = result["stats"]
        graphs = result.get("graphs", {})

        self.update_stats(
            stats["polling_rate_hz"],
            stats.get("avg_jitter_ms", 0)
        )

        self.polling_graph.set_data(graphs.get("polling_rate", []))
        self.jitter_graph.set_data(graphs.get("jitter", []))

        self.log_event("✔ Test finished")

        self.btn_start.setEnabled(True)
        self.lbl_timer.setText("Time left: —")

        self.worker = None
        self.thread = None

        self.save_results()

    # ================= EVENTS =================

    def event(self, e):
        if e.type() == QEvent.Close:
            #rawmouse.stop_capture()
            self.backend.stop_mouse_capture()
            if self.worker:
                self.worker.stop()
            if self.thread:
                self.thread.quit()
                self.thread.wait()

            self.worker = None
            self.thread = None
            e.accept()
        return super().event(e)

    # ================= HELPERS =================

    def log_event(self, text: str):
        self.history.addItem(text)
        self.history.scrollToBottom()

    def update_stats(self, polling: int, jitter: float):
        self.lbl_polling.setText(f"Polling rate: {polling} Hz")
        self.lbl_jitter.setText(f"Average jitter: {jitter}")

    def reset_ui(self):
        self.mouse_panel.reset()
        self.history.clear()
        self.progress.setValue(0)
        self.lbl_timer.setText("Time left: —")
        self.btn_start.setEnabled(True)

    def save_results(self):
        if not self._final_result:
            return

        path = self.backend.get_journal_path(
            test_name=self._final_result["test_name"],
            vid=self._final_result["device"]["vid"],
            pid=self._final_result["device"]["pid"],
        )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._final_result, f, indent=2)

        self.log_event(f"Saved to {path.name}")
