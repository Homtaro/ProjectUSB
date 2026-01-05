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

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        self.device_panel = DevicePanel(backend)
        self.hw_test = HardwareTests(backend)
        self.journal_panel = JournalPanel(backend)

        self.tabs.addTab(self.device_panel, "Devices")
        self.tabs.addTab(self.hw_test, "Hardware Tests")
        self.tabs.addTab(self.journal_panel, "Test Journal")
        #tabs.addTab(WindowsSettingsMenu(), "Demo") #Placeholder

        self.tabs.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tabs)

    def on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if widget is self.journal_panel:
            self.journal_panel.refresh()



