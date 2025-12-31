"""Main entry point for ProjectUSB application."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


from backend import BackendService
from frontend import MainWindow


def main():
    """Run the application."""
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.Highlight, QColor(0, 120, 215))

    app.setPalette(palette)

    # Initialize backend service
    backend_service = BackendService()

    # Create and show main window
    window = MainWindow(backend_service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
