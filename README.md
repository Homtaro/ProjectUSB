# ProjectUSB

Diploma work - A PySide6-based desktop application.

## Project Structure

```
ProjectUSB/
├── backend/                  # Business logic and hardware interaction
│   ├── dlls/                 # Compiled libraries (dinput8.dll, libusb-1.0.dll)
│   ├── modules/              # Sub-modules for hardware diagnostics
│   │   ├── hwTests/          # Hardware-specific test logic (Audio, Gamepad, etc.)
│   │   ├── usbMonitoring.py  # USB device detection and monitoring
│   │   └── usbDecoder.py     # USB descriptor parsing
│   ├── core.py               # Main BackendService coordinator
│   └── __init__.py
├── frontend/                 # UI components and PySide6 windows
│   ├── dialogs/              # Popup selection and configuration dialogs
│   ├── journal/              # Journaling UI (Loaders, entries, and detail views)
│   ├── panels/               # Main UI panels for different hardware tests
│   │   ├── hwTests/          # Test-specific UI (Visualizers, graphs, buttons)
│   │   └── device_panel.py   # General device information panel
│   ├── style/                # Theme and styling (theme.py)
│   ├── main_window.py        # Primary application shell
│   └── __init__.py
├── tools/                    # Utility scripts and USB database files
├── main.py                   # Application entry point
├── requirements.txt          # Primary Python dependencies
├── README.md                 # Project documentation
├── LICENSE                   # Licensing information
└── .gitignore                # Git exclusion rules
```

## Requirements

- Python 3.10+
- PySide6
- requirements.txt

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Homtaro/ProjectUSB.git
   cd ProjectUSB
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python main.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
