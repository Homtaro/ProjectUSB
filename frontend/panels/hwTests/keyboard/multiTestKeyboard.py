from PySide6.QtCore import Qt

from frontend.panels.hwTests.base_window import BaseTestWindow
from frontend.panels.hwTests.keyboard.keyboard_visual import KeyboardVisualPanel

class KeyboardMultiTestWindow(BaseTestWindow):
    def __init__(self, parent=None):
        super().__init__(
            title="Keyboard Multitest",
            subtitle="NKRO, heatmap, key diagnostics",
            parent=parent
        )

        self.setMinimumSize(1300, 600)



        self.keyboard_panel = KeyboardVisualPanel(self)
        self.keyboard_panel.setFocusPolicy(Qt.NoFocus)
        self.layout().addWidget(self.keyboard_panel, 0)
        self.layout().addStretch(1)

        # Testing part ----
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()


    # def keyPressEvent(self, event):
    #     scancode = event.nativeScanCode()
    #     self.keyboard_panel.key_down(scancode)

    def keyPressEvent(self, event):

        vk = event.key()

        if vk == Qt.Key_Print:
            self.keyboard_panel.key_down(0xE037)
            return

        sc = self.normalize_scancode(event)
        self.keyboard_panel.key_down(sc)

    def keyReleaseEvent(self, event):
        sc = self.normalize_scancode(event)
        self.keyboard_panel.key_up(sc)

        # -------------

    def normalize_scancode(self, event):
        vk = event.key()
        sc = event.nativeScanCode()

        if vk == Qt.Key_Up:
            return 0xE048
        if vk == Qt.Key_Down:
            return 0xE050
        if vk == Qt.Key_Left:
            return 0xE04B
        if vk == Qt.Key_Right:
            return 0xE04D

        # if vk == Qt.Key_Print:
        #     return 0xE037

        if vk == Qt.Key_Print:
            self.keyboard_panel.key_down(0xE037)
            return

        if vk == Qt.Key_Pause:
            return 0xE11D

        if vk == Qt.Key_NumLock:
            return 0x45

        return sc