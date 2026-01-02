from PySide6.QtCore import Qt, QThread, QEvent

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

        print("KeyboardMultiTestWindow created", self)

        self.thread: QThread | None = None
        self.worker = None

        self.keyboard_panel = KeyboardVisualPanel(self)
        self.layout().addWidget(self.keyboard_panel, 1)

        self.start_test()

        print(self.backend.get_status())

        self.setMinimumSize(1300, 600)



        #self.keyboard_panel = KeyboardVisualPanel(self)
        self.keyboard_panel.setFocusPolicy(Qt.NoFocus)
        #self.layout().addWidget(self.keyboard_panel, 0)
        self.layout().addStretch(1)

        # Testing part ----
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()


    # def keyPressEvent(self, event):
    #     scancode = event.nativeScanCode()
    #     self.keyboard_panel.key_down(scancode)

    def start_test(self):
        # TODO: later this comes from selected device
        VID = 0x258A
        PID = 0x010C

        self.thread = QThread(self)

        self.worker = self.backend.create_keyboard_test(
            vid=VID,
            pid=PID,
            duration= 0  # 0 = run until stopped
        )

        self.worker.moveToThread(self.thread)

        self.worker.key_down.connect(self.keyboard_panel.key_down)
        self.worker.key_up.connect(self.keyboard_panel.key_up)

        self.thread.started.connect(self.worker.run)
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