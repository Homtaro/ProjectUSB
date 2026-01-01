from frontend.panels.hwTests.base_window import BaseTestWindow

class GamepadMultiTestWindow(BaseTestWindow):
    def __init__(self, parent=None):
        super().__init__(
            title="Gamepad Multitest (X-Input)",
            subtitle="Stick info, deadzones, circular error",
            parent=parent
        )