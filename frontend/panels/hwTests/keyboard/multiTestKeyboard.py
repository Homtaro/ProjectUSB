import json
from datetime import time
from time import strftime

from PySide6.QtCore import Qt, QThread, QEvent, Slot
from PySide6.QtWidgets import QPushButton, QHBoxLayout, QListWidget, QFrame, QVBoxLayout, QLabel, QFileDialog

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

        self.setFixedSize(1320, 750)
        print(self.backend.get_status())
        print("KeyboardMultiTestWindow created", self)

        self.thread: QThread | None = None
        self.worker = None

        self.keyboard_panel = KeyboardVisualPanel(self)
        self.keyboard_panel.setFocusPolicy(Qt.NoFocus)

        # self.keyboard_panel = KeyboardVisualPanel(self)
        # self.layout().addWidget(self.keyboard_panel, 0)

        #self.layout().addWidget(self.keyboard_panel, 0)
        #self.layout().addStretch(1)

        # ---- Bottom area ----
        bottom = QHBoxLayout()

        # === Key history ===
        self.history = QListWidget()
        self.history.setMinimumWidth(300)
        self.history.setFrameShape(QFrame.StyledPanel)

        bottom.addWidget(self.history, 2)

        # === Stats + controls ===
        right = QVBoxLayout()

        def stat_row(title):
            row = QHBoxLayout()
            lbl_title = QLabel(title)
            lbl_value = QLabel("0")
            lbl_title.setMinimumWidth(120)
            row.addWidget(lbl_title)
            row.addWidget(lbl_value)
            return row, lbl_value

        row, self.lbl_pressed = stat_row("Pressed now:")
        right.addLayout(row)

        row, self.lbl_max = stat_row("Max simultaneous:")
        right.addLayout(row)

        row, self.lbl_unique = stat_row("Unique keys:")
        right.addLayout(row)

        row, self.lbl_total = stat_row("Total presses:")
        right.addLayout(row)

        row, self.lbl_nkro = stat_row("NKRO:")
        self.lbl_nkro.setText("NO")
        right.addLayout(row)

        right.addSpacing(1)

        # === Buttons ===
        self.btn_stop = QPushButton("Stop")
        self.btn_reset = QPushButton("Reset")
        self.btn_save = QPushButton("Save")

        right.addWidget(self.btn_stop)
        right.addWidget(self.btn_reset)
        right.addWidget(self.btn_save)
        right.addStretch(1)

        bottom.addLayout(right, 1)

        #self.layout().addLayout(bottom)

        self.start_test()
        # Testing part ----
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        container = QVBoxLayout()
        container.setSpacing(5)  # THIS controls vertical gap
        container.setContentsMargins(0, 0, 0, 0)

        container.addWidget(self.keyboard_panel,0)
        container.addLayout(bottom)

        self.layout().addLayout(container)

        self.btn_stop.clicked.connect(self.stop_test)
        self.btn_reset.clicked.connect(self.reset_test)
        self.btn_save.clicked.connect(lambda: self.save_results(self._final_result))
        self.btn_save.setEnabled(False)

    # ================= SIGNALS =================

    @Slot(dict)
    def update_stats(self, stats):
        self.lbl_pressed.setText(str(stats["pressed_now"]))
        self.lbl_max.setText(str(stats["max_simultaneous"]))
        self.lbl_unique.setText(str(stats["unique_keys"]))
        self.lbl_total.setText(str(stats["total_presses"]))
        self.lbl_nkro.setText("YES" if stats["nkro"] else "NO")

    # def keyPressEvent(self, event):
    #     scancode = event.nativeScanCode()
    #     self.keyboard_panel.key_down(scancode)

    def start_test(self):

        #TODO: Refactor later into a device selection dialog
        VID = 0x258A
        PID = 0x010C

        self.thread = QThread(self)
        self.worker = self.backend.create_keyboard_test(
            vid=VID,
            pid=PID,
            duration=0
        )

        self.worker.moveToThread(self.thread)

        # --- keyboard visual ---
        self.worker.key_down.connect(self.keyboard_panel.key_down)
        self.worker.key_up.connect(self.keyboard_panel.key_up)

        # --- history ---
        self.worker.key_down.connect(lambda sc: self.on_key_event(sc, True))
        self.worker.key_up.connect(lambda sc: self.on_key_event(sc, False))

        # --- stats ---
        self.worker.stats_updated.connect(self.update_stats)

        # --- lifecycle ---
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_test_finished)
        self.worker.finished.connect(self.thread.quit)

        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def event(self, e):
        if e.type() == QEvent.Close:
            print("EVENT Close reached")
            if self.worker:
                self.worker.stop()  # tells backend loop to exit

            if self.thread:
                self.thread.quit()
                self.thread.wait()  # WAIT until run_keyboard_test() returns

            self.worker = None
            self.thread = None

            e.accept()
        return super().event(e)

    def stop_test(self):
        if self.worker:
            self.worker.stop()

    def reset_test(self):
        if self.worker:
            self.worker.stop()

        if self.thread:
            self.thread.quit()
            self.thread.wait()

        self.worker = None
        self.thread = None

        # Clear UI
        self.history.clear()
        self.keyboard_panel.reset()

        self.lbl_pressed.setText("0")
        self.lbl_max.setText("0")
        self.lbl_unique.setText("0")
        self.lbl_total.setText("0")
        self.lbl_nkro.setText("NO")

        self.btn_save.setEnabled(False)

        self.start_test()

    def save_results(self, result):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save keyboard test",
            "keyboard_test.json",
            "JSON Files (*.json)"
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    def on_test_finished(self, result):
        self._final_result = result
        self.btn_save.setEnabled(True)

    def on_key_event(self, scancode, is_down):
        ts = strftime("%H:%M:%S")
        text = f"[{ts}] {'DOWN' if is_down else 'UP'} 0x{scancode:X}"
        self.history.addItem(text)
        self.history.scrollToBottom()

    # def closeEvent(self, event):
    #
    #     print("Closing keyboard test window")
    #
    #     if self.worker:
    #         self.worker.stop()  # tells backend loop to exit
    #
    #     if self.thread:
    #         self.thread.quit()
    #         self.thread.wait()  # WAIT until run_keyboard_test() returns
    #
    #     self.worker = None
    #     self.thread = None
    #
    #     event.accept()

    # def keyPressEvent(self, event):
    #     sc = self.normalize_scancode(event)
    #     if sc is not None:
    #         self.keyboard_panel.key_down(sc)
    #
    # def keyReleaseEvent(self, event):
    #     sc = self.normalize_scancode(event)
    #     if sc is not None:
    #         self.keyboard_panel.key_up(sc)
    #
    #     # -------------
    #
    # def normalize_scancode(self, event):
    #     vk = event.key()
    #     sc = event.nativeScanCode()
    #
    #     # Arrow keys
    #     if vk == Qt.Key_Up:
    #         return 0xE048
    #     if vk == Qt.Key_Down:
    #         return 0xE050
    #     if vk == Qt.Key_Left:
    #         return 0xE04B
    #     if vk == Qt.Key_Right:
    #         return 0xE04D
    #
    #     # Print Screen (RELEASE ONLY WORKS)
    #     if vk == Qt.Key_Print:
    #         return 0xE037
    #
    #     # Pause
    #     if vk == Qt.Key_Pause:
    #         return 0xE11D
    #
    #     # NumLock
    #     if vk == Qt.Key_NumLock:
    #         return 0x45
    #
    #     return sc