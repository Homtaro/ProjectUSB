"""Main entry point for ProjectUSB application."""

import sys

from PySide6.QtWidgets import QApplication

from backend import BackendService
from frontend import MainWindow


def main():
    """Run the application."""
    app = QApplication(sys.argv)

    # Initialize backend service
    backend_service = BackendService()

    # Create and show main window
    window = MainWindow(backend_service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
