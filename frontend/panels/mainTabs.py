from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from frontend.panels.device_panel import DevicePanel
from frontend.panels.device_HWpanel import HardwareTests
from frontend.panels.device_wip_pane_demo import WindowsSettingsMenu
from frontend.panels.device_test_journal import JournalPanel


class MainPanel(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)

        self.device_panel = DevicePanel(backend)
        self.hw_test = HardwareTests(backend)
        self.journal_panel = JournalPanel(backend)

        tabs.addTab(self.device_panel, "Devices")
        tabs.addTab(self.hw_test, "Hardware Tests")
        tabs.addTab(self.journal_panel, "Test Journal")
        #tabs.addTab(WindowsSettingsMenu(), "Demo") #Placeholder

        layout.addWidget(tabs)



