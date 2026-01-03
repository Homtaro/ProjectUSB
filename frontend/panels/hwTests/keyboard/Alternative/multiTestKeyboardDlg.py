import json
from time import strftime

from PySide6.QtCore import Qt, QThread, QEvent, Slot, QTimer
from PySide6.QtWidgets import (
    QPushButton,
    QHBoxLayout,
    QListWidget,
    QFrame,
    QVBoxLayout,
    QLabel,
)

from frontend.panels.hwTests.base_window import BaseTestWindow
from frontend.panels.hwTests.keyboard.keyboard_visual import KeyboardVisualPanel


class KeyboardMultiTestWindow(BaseTestWindow):
    """
    Keyboard Multitest window.
    Assumes a valid HID keyboard (VID/PID) is already selected.
    """

    def __init__(self, backend, vid: int, pid: int, parent=None):
        assert vid is not None and pid is not None, "KeyboardMultiTestWindow requires VID/PID"

        super().__init__(
            backend=backend,
            title="Keyboard Multitest",
            subtitle="NKRO, heatmap, key diagnostics",
            parent=parent,
        )

        self.setFixedSize(1320, 750)

        self.vid = vid
        self.pid = pid

        self.thread: QThread | None = None
        self.worker = None
        self._final_result = None

        # ================= UI TIMER =================
        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(33)  # ~30 FPS
        self.ui_timer.timeout.connect(self.refresh_ui)
        self.ui_timer.start()

        # ================= KEYBOARD VISUAL =================
        self.keyboard_panel = KeyboardVisualPanel(self)
        self.keyboard_panel.setFocusPolicy(Qt.NoFocus)

        # ================= BOTTOM AREA =================
        bottom = QHBoxLayout()

        # ---- History ----
        self.history = QListWidget()
        self.history.setMinimumWidth(300)
        self.history.setFrameShape(QFrame.StyledPanel)
        self.history.setFocusPolicy(Qt.NoFocus)
        bottom.addWidget(self.history, 2)

        # ---- Stats + Controls ----
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

        right.addSpacing(10)

        # ---- Buttons ----
        self.btn_stop = QPushButton("Stop")
        self.btn_reset = QPushButton("Reset")
        self.btn_save = QPushButton("Save")

        for btn in (self.btn_stop, self.btn_reset, self.btn_save):
            btn.setFocusPolicy(Qt.NoFocus)

        right.addWidget(self.btn_stop)
        right.addWidget(self.btn_reset)
        right.addWidget(self.btn_save)
        right.addStretch(1)

        bottom.addLayout(right, 1)

        # ================= MAIN LAYOUT =================
        container = QVBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.setSpacing(5)

        container.addWidget(self.keyboard_panel)
        container.addLayout(bottom)

        self.layout().addLayout(container)

        # ================= BUTTON WIRING =================
        self.btn_stop.clicked.connect(self.stop_test)
        self.btn_reset.clicked.connect(self.reset_test)
        self.btn_save.clicked.connect(lambda: self.save_results(self._final_result))

        self.btn_save.setEnabled(False)
        self.btn_reset.setEnabled(False)

        # Disable TAB focus traversal
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        # ================= START TEST =================
        self.start_test()

    # =========================================================
    # ======================= TEST ============================
    # =========================================================

    def start_test(self):
        self.thread = QThread(self)
        self.worker = self.backend.create_keyboard_test(
            vid=self.vid,
            pid=self.pid,
            duration=0,
        )

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_test_finished)
        self.worker.finished.connect(self.thread.quit)

        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        self.btn_stop.setEnabled(True)
        self.btn_reset.setEnabled(False)
        self.btn_save.setEnabled(False)

    def stop_test(self):
        if not self.worker:
            return
        self.btn_stop.setEnabled(False)
        self.worker.stop()

    def reset_test(self):
        if self.worker:
            return  # wait for finished signal

        self.history.clear()
        self.keyboard_panel.reset()

        for lbl in (
            self.lbl_pressed,
            self.lbl_max,
            self.lbl_unique,
            self.lbl_total,
        ):
            lbl.setText("0")

        self.lbl_nkro.setText("NO")

        self.start_test()

    # =========================================================
    # ======================= UI ==============================
    # =========================================================

    def refresh_ui(self):
        if not self.worker:
            return

        for event_type, scancode in self.worker.pop_events(100):
            if event_type == "down":
                self.keyboard_panel.key_down(scancode)
                self.add_history(scancode, True)
            else:
                self.keyboard_panel.key_up(scancode)
                self.add_history(scancode, False)

        stats = self.worker.get_stats()
        if stats:
            self.update_stats(stats)

    @Slot(dict)
    def update_stats(self, stats):
        self.lbl_pressed.setText(str(stats["pressed_now"]))
        self.lbl_max.setText(str(stats["max_simultaneous"]))
        self.lbl_unique.setText(str(stats["unique_keys"]))
        self.lbl_total.setText(str(stats["total_presses"]))
        self.lbl_nkro.setText("YES" if stats["nkro"] else "NO")

    def add_history(self, scancode, is_down):
        ts = strftime("%H:%M:%S")
        key_name = self.backend.resolve_scancode(scancode)
        self.history.addItem(
            f"[{ts}] {'DOWN' if is_down else 'UP'} 0x{scancode:X} [{key_name}]"
        )
        self.history.scrollToBottom()

    # =========================================================
    # ======================= SAVE ============================
    # =========================================================

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

        print(f"Saved test to {path}")

    def on_test_finished(self, result):
        self._final_result = result

        self.btn_save.setEnabled(True)
        self.btn_reset.setEnabled(True)
        self.btn_stop.setEnabled(False)

        self.worker = None
        self.thread = None

    # =========================================================
    # ======================= FOCUS ===========================
    # =========================================================

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            event.accept()
            return
        super().keyPressEvent(event)

    def event(self, e):
        if e.type() == QEvent.Close:
            if self.worker:
                self.worker.stop()
            if self.thread:
                self.thread.quit()
                self.thread.wait()
        return super().event(e)
