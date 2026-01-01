from frontend.panels.hwTests.base_window import BaseTestWindow

class MouseMultiTestWindow(BaseTestWindow):
    def __init__(self, parent=None):
        super().__init__(
            title="Mouse Multitest",
            subtitle="Heatmap, polling rate, jitter",
            parent=parent
        )
