from frontend.panels.hwTests.base_window import BaseTestWindow


class SingleFileStorageTestWindow(BaseTestWindow):
    def __init__(self, parent=None):
        super().__init__(
            title="Single File Storage Test",
            subtitle="Read/write benchmark with hash verification",
            parent=parent
        )