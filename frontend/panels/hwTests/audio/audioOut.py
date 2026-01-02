from frontend.panels.hwTests.base_window import BaseTestWindow

class AudioOutputTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Audio Playback Test",
            subtitle="Left / right channel diagnostics",
            parent=parent
        )