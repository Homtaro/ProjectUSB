<div align="center">

# 🚀 ProjectUSB
### Hardware Diagnostic & Monitoring Suite

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Diploma%20Project-orange)]()

**A comprehensive, high-performance interface for real-time monitoring and testing of USB and system peripherals.**

</div>

---

## 📖 About
**ProjectUSB** is a desktop application developed as a diploma project. Built with **Python 3.12** and **PySide6**, it utilizes a multi-threaded architecture to provide non-blocking hardware polling and low-level interaction tests.

It is designed to detect, decode, and benchmark a wide variety of hardware including Gamepads, Audio interfaces, HID peripherals, and external storage.

---

## ✨ Key Features

### 🎮 Multi-Device Diagnostics
Dedicated testing modules for specialized hardware:
* **Gamepads:** Real-time **X-Input** monitoring with circularity error analysis and stick drift detection.
* **Audio:** Signal analysis for input devices (**WASAPI**) including Peak/RMS levels and signal presence verification.
* **HID Peripherals:** Low-level interaction tests for keyboards and mice.
* **Storage:** Speed and reliability benchmarking for external drives.

### 🔌 USB Monitoring Engine
* **Advanced Backend:** Detects and decodes USB device trees.
* **Deep Analysis:** Parses interface classes and raw hardware descriptors in real-time.

### 💾 Persistent Journaling System
* **Auto-Save:** Automatically saves detailed JSON reports of every test session.
* **Journal Viewer:** A built-in UI to review historical diagnostics, compare device performance, and export results.

### 🎨 Modern UI/UX
* **Dark Theme:** A sleek, responsive interface designed for long debugging sessions.
* **Custom Widgets:** Features analog bar visualizers, stick coordinate mappers, and custom graphs.

---

## 🛠 Technical Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **GUI Framework** | PySide6 | Qt for Python, utilizing custom widgets and styles. |
| **Language** | Python 3.12 | Core logic and scripting. |
| **Backend** | Threading | Multi-threaded architecture for non-blocking I/O. |
| **Low-Level** | WinAPI / CTypes | Integration with WASAPI, X-Input, and raw USB descriptors. |
| **Data** | JSON | Structured logging and reporting format. |

---

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
