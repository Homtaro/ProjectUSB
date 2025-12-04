"""Main window for ProjectUSB application."""

from PySide6.QtCore import Qt
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
        """Set up the user interface."""
        self.setWindowTitle("ProjectUSB")
        self.setMinimumSize(600, 400)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Status label
        self._status_label = QLabel(self._backend.get_status())
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        # Input section
        input_layout = QHBoxLayout()
        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("Enter data to process...")
        self._input_field.returnPressed.connect(self._on_process_clicked)
        input_layout.addWidget(self._input_field)

        self._process_button = QPushButton("Process")
        self._process_button.clicked.connect(self._on_process_clicked)
        input_layout.addWidget(self._process_button)

        layout.addLayout(input_layout)

        # Output section
        output_label = QLabel("Output:")
        layout.addWidget(output_label)

        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        layout.addWidget(self._output_text)

    def _on_process_clicked(self):
        """Handle the process button click."""
        input_data = self._input_field.text()
        if input_data:
            result = self._backend.process_data(input_data)
            self._output_text.append(result)
            self._input_field.clear()
