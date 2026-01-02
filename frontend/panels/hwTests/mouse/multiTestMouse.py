from frontend.panels.hwTests.base_window import BaseTestWindow

class MouseMultiTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Mouse Multitest",
            subtitle="Heatmap, polling rate, jitter",
            parent=parent
        )
