from frontend.panels.hwTests.base_window import BaseTestWindow

class AudioInputTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Microphone Test",
            subtitle="Record & playback diagnostics",
            parent=parent
        )
