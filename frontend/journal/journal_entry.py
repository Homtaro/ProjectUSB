from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class JournalEntry:
    path: Path

    # normalized fields
    date: str
    timestamp: float
    category: str
    test_name: str
    device_name: str
    pid_vid: str

    raw: dict
