from frontend.panels.hwTests.base_window import BaseTestWindow

class GamepadMultiTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Gamepad Multitest (X-Input)",
            subtitle="Stick info, deadzones, circular error",
            parent=parent
        )