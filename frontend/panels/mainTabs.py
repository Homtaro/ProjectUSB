from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from frontend.panels.device_panel import DevicePanel
from frontend.panels.device_HWpanel import HardwareTests
from frontend.panels.device_wip_pane_demo import WindowsSettingsMenu
from frontend.panels.device_test_journal import JournalPanel


class MainPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)

        tabs.addTab(DevicePanel(), "Devices")
        tabs.addTab(HardwareTests(), "Hardware Tests")  # placeholder
        tabs.addTab(JournalPanel(), "Test Journal")  # later
        tabs.addTab(WindowsSettingsMenu(), "Demo")    # later

        layout.addWidget(tabs)



