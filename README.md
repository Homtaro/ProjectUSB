# ProjectUSB

Diploma work - A PySide6-based desktop application.

## Project Structure

```
ProjectUSB/
├── backend/          # Backend module for business logic
│   ├── __init__.py
│   └── core.py       # Core backend service
├── frontend/         # Frontend module for UI components
│   ├── __init__.py
│   └── main_window.py  # Main application window
├── main.py           # Application entry point
├── requirements.txt  # Python dependencies
└── README.md
```

## Requirements

- Python 3.10+
- PySide6

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
