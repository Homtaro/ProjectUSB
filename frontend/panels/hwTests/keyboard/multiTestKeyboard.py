import json
from time import strftime

from PySide6.QtCore import Qt, QThread, QEvent, Slot, QTimer
from PySide6.QtWidgets import (
    QPushButton, QHBoxLayout, QListWidget, QFrame,
    QVBoxLayout, QLabel, QDialog
)

from frontend.dialogs.device_selection import DeviceSelectionDialog
from frontend.panels.hwTests.base_window import BaseTestWindow
from frontend.panels.hwTests.keyboard.keyboard_visual import KeyboardVisualPanel


class KeyboardMultiTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Keyboard Multitest",
            subtitle="NKRO, heatmap, key diagnostics",
            parent=parent
        )

        self.setVisible(False)
        self.setFixedSize(1320, 750)

        self.thread: QThread | None = None
        self.worker = None

        self._final_result = None
        self.selected_vid = None
        self.selected_pid = None

        # ================= UI TIMER =================

        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(33)
        self.ui_timer.timeout.connect(self.refresh_ui)
        self.ui_timer.start()

        # ================= UI =================

        self.keyboard_panel = KeyboardVisualPanel(self)
        self.keyboard_panel.setFocusPolicy(Qt.NoFocus)

        bottom = QHBoxLayout()

        self.history = QListWidget()
        self.history.setMinimumWidth(300)
        self.history.setFrameShape(QFrame.StyledPanel)
        bottom.addWidget(self.history, 2)

        right = QVBoxLayout()

        def stat_row(title):
            row = QHBoxLayout()
            lbl_title = QLabel(title)
            lbl_value = QLabel("0")
            lbl_title.setMinimumWidth(120)
            row.addWidget(lbl_title)
            row.addWidget(lbl_value)
            return row, lbl_value

        _, self.lbl_pressed = stat_row("Pressed now:")
        right.addLayout(_)
        _, self.lbl_max = stat_row("Max simultaneous:")
        right.addLayout(_)
        _, self.lbl_unique = stat_row("Unique keys:")
        right.addLayout(_)
        _, self.lbl_total = stat_row("Total presses:")
        right.addLayout(_)
        _, self.lbl_nkro = stat_row("NKRO:")
        self.lbl_nkro.setText("NO")
        right.addLayout(_)

        right.addSpacing(1)

        self.btn_stop = QPushButton("Stop")
        self.btn_reset = QPushButton("Reset")
        self.btn_save = QPushButton("Save")

        self.setStyleSheet("""
            QPushButton { padding: 6px; }
            QPushButton:disabled {
                border: 2px solid #a33;
                color: #777;
                background-color: #1a1a1a;
            }
        """)

        right.addWidget(self.btn_stop)
        right.addWidget(self.btn_reset)
        right.addWidget(self.btn_save)
        right.addStretch(1)

        bottom.addLayout(right, 1)

        container = QVBoxLayout()
        container.setSpacing(5)
        container.setContentsMargins(0, 0, 0, 0)
        container.addWidget(self.keyboard_panel, 0)
        container.addLayout(bottom)

        self.layout().addLayout(container)

        # ================= SIGNALS =================

        self.btn_stop.clicked.connect(self.stop_test)
        self.btn_reset.clicked.connect(self.reset_test)
        self.btn_save.clicked.connect(lambda: self.save_results(self._final_result))
        self.btn_save.setEnabled(False)
        self.btn_reset.setEnabled(False)

        QTimer.singleShot(0, self.select_device_and_start)

    # ================= DEVICE SELECTION =================

    def select_device_and_start(self):
        devices = self.backend.get_hid_keyboards()
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
        self.start_test()

    # ================= RAW INPUT BRIDGE =================
    # MAIN THREAD → WORKER

    def on_raw_key_event(self, event_type, scancode):
        if self.worker:
            self.worker.handle_event(event_type, scancode)

    # ================= TEST START =================

    def start_test(self):
        if self.worker:
            return

        self.thread = QThread(self)
        self.worker = self.backend.create_keyboard_test(
            vid=self.selected_vid,
            pid=self.selected_pid,
            duration=0
        )

        self.worker.moveToThread(self.thread)

        self.worker.finished.connect(self.on_test_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        # ---- RAW INPUT (MAIN THREAD) ----
        self.backend.start_keyboard_capture(
            vid=self.selected_vid,
            pid=self.selected_pid,
            event_callback=self.on_raw_key_event,
            running_check=lambda: self.worker and self.worker._running
        )

    # ================= UI UPDATE =================

    def refresh_ui(self):
        if not self.worker:
            return

        for event_type, scancode in self.worker.pop_events(100):
            if event_type == "down":
                self.keyboard_panel.key_down(scancode)
                self.keyboard_panel.keys[scancode].hit()
                self.add_history(scancode, True)
            else:
                self.keyboard_panel.key_up(scancode)
                self.add_history(scancode, False)

        stats = self.worker.get_stats()
        if stats:
            self.update_stats(stats)

        self.keyboard_panel.update_heatmap()

    # ================= STATS =================

    @Slot(dict)
    def update_stats(self, stats):
        self.lbl_pressed.setText(str(stats["pressed_now"]))
        self.lbl_max.setText(str(stats["max_simultaneous"]))
        self.lbl_unique.setText(str(stats["unique_keys"]))
        self.lbl_total.setText(str(stats["total_presses"]))
        self.lbl_nkro.setText("YES" if stats["nkro"] else "NO")

    # ================= STOP / RESET =================

    def stop_test(self):
        if not self.worker:
            return

        self.btn_stop.setEnabled(False)

        self.backend.stop_keyboard_capture()

        self.worker.stop()

        self.worker.finalize()

    def reset_test(self):
        if self.worker:
            return

        self.history.clear()
        self.keyboard_panel.reset()
        self.lbl_pressed.setText("0")
        self.lbl_max.setText("0")
        self.lbl_unique.setText("0")
        self.lbl_total.setText("0")
        self.lbl_nkro.setText("NO")

        self.btn_save.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_reset.setEnabled(False)

        self.start_test()

    # ================= FINISH =================

    def on_test_finished(self, result):
        self._final_result = result
        self.btn_save.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_reset.setEnabled(True)

        self.worker = None
        self.thread = None

    # ================= HELPERS =================

    def add_history(self, scancode, is_down):
        ts = strftime("%H:%M:%S")
        key_name = self.backend.resolve_scancode(scancode)
        self.history.addItem(
            f"[{ts}] {'DOWN' if is_down else 'UP'} 0x{scancode:X} [{key_name}]"
        )
        self.history.scrollToBottom()

    def save_results(self, result):
        if not result:
            return

        path = self.backend.get_journal_path(
            test_name=result["test_name"],
            vid=result["device"]["vid"],
            pid=result["device"]["pid"],
        )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    def event(self, e):
        if e.type() == QEvent.Close:
            self.backend.stop_keyboard_capture()
            if self.worker:
                self.worker.stop()
            if self.thread:
                self.thread.quit()
                self.thread.wait()

            self.worker = None
            self.thread = None
            e.accept()
        return super().event(e)
