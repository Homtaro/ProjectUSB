from frontend.panels.hwTests.base_window import BaseTestWindow

class AudioInputTestWindow(BaseTestWindow):
    def __init__(self, parent=None):
        super().__init__(
            title="Microphone Test",
            subtitle="Record & playback diagnostics",
            parent=parent
        )