import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QFrame, QSizePolicy, QStackedWidget, QLineEdit)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QFont, QColor, QPalette


class SettingsCategoryButton(QWidget):
    def __init__(self, icon_name, title, description, parent=None):
        super().__init__(parent)

        # Main layout with proper margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 3, 0, 3)  # Add vertical padding between buttons
        main_layout.setSpacing(0)

        # Button container
        self.button = QPushButton()
        self.button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Use QHBoxLayout with proper constraints
        button_layout = QHBoxLayout(self.button)
        button_layout.setContentsMargins(12, 12, 12, 12)
        button_layout.setSpacing(12)

        # Icon placeholder
        icon_label = QLabel()
        icon_label.setFixedSize(QSize(24, 24))
        icon_label.setStyleSheet("""
            background-color: #0078d7; 
            border-radius: 12px;
        """)

        # Create a container widget for the text to ensure proper sizing
        text_container = QWidget()
        text_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        # Labels with proper sizing and explicit colors
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 10))
        self.title_label.setStyleSheet("color: #ffffff; background-color: transparent;")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.desc_label = QLabel(description)
        self.desc_label.setFont(QFont("Segoe UI", 9))
        self.desc_label.setStyleSheet("color: #b0b0b0; background-color: transparent;")
        self.desc_label.setWordWrap(True)
        self.desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Add labels to text layout
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.desc_label)

        # Add widgets to button layout
        button_layout.addWidget(icon_label)
        button_layout.addWidget(text_container, 1)  # Give text container stretch priority

        # Add button to main layout
        main_layout.addWidget(self.button)

        # Button styling
        self.button.setFlat(True)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
        """)

        # Set proper minimum height for the entire widget
        # self.setMinimumHeight(76)  # 70px for button + 6px for margins

        # Connect signals
        self.button.clicked.connect(self.on_clicked)

    def on_clicked(self):
        animation = QPropertyAnimation(self.button, b"styleSheet")
        animation.setDuration(200)
        animation.setStartValue("""
            QPushButton {
                background-color: #505050;
                border: none;
                border-radius: 4px;
                text-align: left;
                padding: 8px;
                min-height: 70px;
            }
        """)
        animation.setEndValue("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                text-align: left;
                padding: 8px;
                min-height: 70px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
        """)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()


class CustomSearchBox(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Find a setting")
        self.setFixedHeight(35)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #202020;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding-left: 35px;
                color: #ffffff;
                selection-background-color: #0078d7;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
        """)

        # Search icon
        self.search_icon = QLabel(self)
        self.search_icon.setText("🔍")
        self.search_icon.setStyleSheet("color: #808080; background-color: transparent;")
        self.search_icon.setGeometry(10, 8, 20, 20)


class WindowsSettingsMenu(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Windows Settings")
        self.setGeometry(100, 100, 1000, 650)

        # Set dark theme palette
        self.set_dark_theme()

        # Main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel (categories)
        left_widget = QWidget()
        left_widget.setMinimumWidth(360)  # Increased minimum width
        left_widget.setStyleSheet("""
            background-color: #1e1e1e;
            border-right: 1px solid #303030;
        """)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(16, 20, 16, 20)
        left_layout.setSpacing(16)

        # Header
        header = QLabel("Settings")
        header.setFont(QFont("Segoe UI Semibold", 22))
        header.setStyleSheet("color: #ffffff;")

        # Search box
        search_box = CustomSearchBox()

        # Add header and search
        left_layout.addWidget(header)
        left_layout.addWidget(search_box)
        left_layout.addSpacing(10)

        # Create scrollable area for categories
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #606060;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Container for category buttons with proper spacing
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        category_layout = QVBoxLayout(scroll_content)
        category_layout.setContentsMargins(0, 5, 5, 5)  # Add right margin for scrollbar
        category_layout.setSpacing(0)  # Spacing is handled within button widgets

        # Add category buttons
        categories = [
            ("System", "Display, sound, notifications, power"),
            ("Devices", "Bluetooth, printers, mouse"),
            ("Phone", "Link your Android, iPhone"),
            ("Network & Internet", "Wi-Fi, airplane mode, VPN"),
            ("Personalization", "Background, lock screen, colors"),
            ("Apps", "Uninstall, defaults, optional features"),
            ("Accounts", "Your accounts, email, sync, work, family"),
            ("Time & Language", "Speech, region, date"),
            ("Gaming", "Game bar, captures, broadcasting"),
            ("Ease of Access", "Narrator, magnifier, high contrast"),
            ("Search", "Find my files, permissions"),
            ("Privacy", "Location, camera, microphone"),
            ("Update & Security", "Windows Update, recovery, backup")
        ]

        for title, desc in categories:
            btn = SettingsCategoryButton("icon", title, desc)
            category_layout.addWidget(btn)

        # Add stretch to push buttons to the top
        category_layout.addStretch(1)

        # Set the scroll content
        scroll_area.setWidget(scroll_content)
        left_layout.addWidget(scroll_area, 1)

        # Right panel (content area)
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: #121212;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(40, 40, 40, 40)

        # Add placeholder content with Windows 10 style
        content_title = QLabel("Welcome to Settings")
        content_title.setFont(QFont("Segoe UI Semibold", 28))
        content_title.setStyleSheet("color: #ffffff; margin-bottom: 15px;")

        content_subtitle = QLabel("Customize and configure your Windows experience")
        content_subtitle.setFont(QFont("Segoe UI", 14))
        content_subtitle.setStyleSheet("color: #b0b0b0; margin-bottom: 30px;")

        instruction = QLabel("Select a category from the menu on the left to get started")
        instruction.setFont(QFont("Segoe UI", 12))
        instruction.setStyleSheet("color: #909090;")

        right_layout.addWidget(content_title)
        right_layout.addWidget(content_subtitle)
        right_layout.addWidget(instruction)
        right_layout.addStretch(1)

        # Add panels to main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)

        self.setCentralWidget(main_widget)

    def set_dark_theme(self):
        dark_palette = QPalette()

        # Set color roles from a dark palette
        dark_palette.setColor(QPalette.Window, QColor(18, 18, 18))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(15, 15, 15))
        dark_palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(0, 120, 215))
        dark_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        # Apply the palette
        self.setPalette(dark_palette)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # More consistent cross-platform style

    # Enable high DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    window = WindowsSettingsMenu()
    window.show()
    sys.exit(app.exec())