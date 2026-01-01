from frontend.panels.hwTests.base_window import BaseTestWindow

class AudioOutputTestWindow(BaseTestWindow):
    def __init__(self, parent=None):
        super().__init__(
            title="Audio Playback Test",
            subtitle="Left / right channel diagnostics",
            parent=parent
        )