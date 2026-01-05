"""Main window for ProjectUSB application."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backend import BackendService
from frontend.panels.mainTabs import MainPanel


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, backend_service: BackendService):
        """Initialize the main window.

        Args:
            backend_service: The backend service instance to use.
        """
        super().__init__()
        self._backend = backend_service
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("ProjectUSB")
        self.setFixedSize(1000, 600)

       # self.device_panel = DevicePanel()
       # self.setCentralWidget(self.device_panel)

        self.main_panel = MainPanel(self._backend)
        self.setCentralWidget(self.main_panel)

    def _on_process_clicked(self):
        """Handle the process button click."""
        input_data = self._input_field.text()
        if input_data:
            result = self._backend.process_data(input_data)
            self._output_text.append(result)
            self._input_field.clear()

    def closeEvent(self, event: QCloseEvent):
        try:
            #select HardwareTests panel
            hw_panel = self.main_panel.hw_test
            hw_panel.close_all_test_windows()
        except AttributeError:
            pass

        event.accept()