from frontend.panels.hwTests.base_window import BaseTestWindow


class SingleFileStorageTestWindow(BaseTestWindow):
    def __init__(self, backend, parent=None):
        super().__init__(
            backend=backend,
            title="Single File Storage Test",
            subtitle="Read/write benchmark with hash verification",
            parent=parent
        )