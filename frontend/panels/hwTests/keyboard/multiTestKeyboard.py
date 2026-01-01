from frontend.panels.hwTests.base_window import BaseTestWindow


class KeyboardMultiTestWindow(BaseTestWindow):
    def __init__(self, parent=None):
        super().__init__(
            title="Keyboard Multitest",
            subtitle="NKRO, heatmap, key diagnostics",
            parent=parent
        )
