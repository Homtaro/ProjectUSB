from frontend.panels.hwTests.base_window import BaseTestWindow

class MultiFileStorageTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Multiple Files Storage Test",
            subtitle="Batch read/write benchmark with hash verification",
            parent=parent
        )