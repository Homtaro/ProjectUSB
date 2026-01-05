import json

from PySide6.QtCore import Qt, QThread, QEvent, QTimer
from PySide6.QtWidgets import (
    QListWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QFrame
)

from frontend.panels.hwTests.base_window import BaseTestWindow


class AudioInputTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Microphone Test",
            subtitle="Record & playback diagnostics",
            parent=parent
        )

        self._final_result = None

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

        lbl_devices = QLabel("Input devices (WASAPI)")
        lbl_devices.setStyleSheet("font-weight: bold;")

        self.device_list = QListWidget()
        self.device_list.setMinimumWidth(350)

        self.btn_refresh = QPushButton("Refresh devices")
        self.btn_refresh.setFixedHeight(26)

        left.addWidget(lbl_devices)
        left.addWidget(self.device_list, 1)
        left.addWidget(self.btn_refresh)

        # ==================================================
        # RIGHT: CONTROLS + STATS
        # ==================================================
        right = QVBoxLayout()
        right.setSpacing(8)

        lbl_controls = QLabel("Controls")
        lbl_controls.setStyleSheet("font-weight: bold;")

        self.btn_record = QPushButton("Record (5s)")
        self.btn_playback = QPushButton("Playback")

        self.btn_record.setFixedHeight(28)
        self.btn_playback.setFixedHeight(28)
        self.btn_playback.setEnabled(False)

        self.lbl_status = QLabel("Idle")
        self.lbl_status.setStyleSheet("color: #aaaaaa;")

        # ---- Stats panel ----
        stats = QFrame()
        stats.setFrameShape(QFrame.StyledPanel)
        stats_layout = QVBoxLayout(stats)

        stats_title = QLabel("Signal analysis")
        stats_title.setStyleSheet("font-weight: bold;")

        self.lbl_peak = QLabel("Peak level: —")
        self.lbl_rms = QLabel("RMS level: —")
        self.lbl_signal = QLabel("Signal present: —")

        for lbl in (self.lbl_peak, self.lbl_rms, self.lbl_signal):
            lbl.setStyleSheet("color: #cccccc;")

        stats_layout.addWidget(stats_title)
        stats_layout.addWidget(self.lbl_peak)
        stats_layout.addWidget(self.lbl_rms)
        stats_layout.addWidget(self.lbl_signal)

        # ---- Assemble right ----
        right.addWidget(lbl_controls)
        right.addWidget(self.btn_record)
        right.addWidget(self.btn_playback)
        right.addWidget(self.lbl_status)
        right.addSpacing(6)
        right.addWidget(stats)
        right.addStretch(1)

        # ================= FINAL =================
        root.addLayout(left, 1)
        root.addLayout(right, 1)
        self.layout().addLayout(root)

        # ================= SIGNALS =================
        self.btn_refresh.clicked.connect(self.refresh_devices)
        self.btn_record.clicked.connect(self.start_record)
        self.btn_playback.clicked.connect(self.playback)

        self.refresh_devices()

    # ==================================================
    # DEVICE MANAGEMENT
    # ==================================================

    def refresh_devices(self):
        self.device_list.clear()
        for idx, name in self.backend.list_audio_input_devices():
            self.device_list.addItem(f"{idx}: {name}")

    # ==================================================
    # RECORDING
    # ==================================================

    def start_record(self):
        if not self.device_list.currentItem():
            return

        idx = int(self.device_list.currentItem().text().split(":")[0])

        self.btn_record.setEnabled(False)
        self.btn_playback.setEnabled(False)
        self.lbl_status.setText("Recording…")

        self.thread = QThread(self)
        self.worker = self.backend.create_audio_input_test(idx)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.record)

        self.worker.recorded.connect(self.on_record_finished)
        self.worker.error.connect(self.on_error)

        self.thread.start()

    def on_record_finished(self, _):
        self.lbl_status.setText("Analyzing…")
        self.worker.analyzed.connect(self.update_stats)
        self.worker.analyze()

        self.btn_record.setEnabled(True)
        self.btn_playback.setEnabled(True)
        self.lbl_status.setText("Ready")

        self.thread.quit()
        self.thread = None

    # ==================================================
    # PLAYBACK
    # ==================================================

    def playback(self):
        if not self.worker:
            return

        self.btn_record.setEnabled(False)
        self.btn_playback.setEnabled(False)
        self.btn_refresh.setEnabled(False)

        self.lbl_status.setText("Playing back…")

        self.worker.playback()

        # Poll playback state without blocking UI
        self._play_timer = QTimer(self)
        self._play_timer.setInterval(50)
        self._play_timer.timeout.connect(self._check_playback_finished)
        self._play_timer.start()

    def _check_playback_finished(self):
        import sounddevice as sd

        if not sd.get_stream().active:
            self._play_timer.stop()
            self._play_timer.deleteLater()

            self.lbl_status.setText("Ready")
            self.btn_record.setEnabled(True)
            self.btn_playback.setEnabled(True)
            self.btn_refresh.setEnabled(True)

    # ==================================================
    # UI HELPERS
    # ==================================================

    def update_stats(self, stats):
        self._final_result = stats

        self.lbl_peak.setText(f"Peak level: {stats['result']['peak']}")
        self.lbl_rms.setText(f"RMS level: {stats['result']['rms']}")
        self.lbl_signal.setText(
            f"Signal present: {'YES' if stats['result']['signal'] else 'NO'}"
        )

        self.save_results()

    def save_results(self):
        if not self._final_result:
            return

        device = self._final_result.get("device", {})

        path = self.backend.get_journal_path_device(
            test_name=self._final_result["test_name"],
            device=device,
        )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._final_result, f, indent=2)

        print(f"Saved audio input test to {path.name}")

    def on_error(self, msg):
        print("Audio input error:", msg)
        self.lbl_status.setText("Error")
        self.btn_record.setEnabled(True)
        self.btn_playback.setEnabled(False)

    def event(self, e):
        if e.type() == QEvent.Close:
            if self.thread and self.thread.isRunning():
                try:
                    self.thread.quit()
                    self.thread.wait(3000)
                except Exception:
                    pass

            self.thread = None
            self.worker = None
            e.accept()
            return True

        return super().event(e)
