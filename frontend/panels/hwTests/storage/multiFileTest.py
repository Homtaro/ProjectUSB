from frontend.panels.hwTests.base_window import BaseTestWindow

class MultiFileStorageTestWindow(BaseTestWindow):
    def __init__(self, parent=None):
        super().__init__(
            title="Multiple Files Storage Test",
            subtitle="Batch read/write benchmark with hash verification",
            parent=parent
        )