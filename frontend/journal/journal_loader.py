import json
import re
from pathlib import Path
from datetime import datetime

from .journal_entry import JournalEntry


TEST_CATEGORY_MAP = {
    "Keyboard": "Keyboard",
    "Mouse": "Mouse",
    "Gamepad": "Gamepad",
    "Audio": "Audio",
    "Storage": "Storage",
}


def infer_category(test_name: str) -> str:
    for key, cat in TEST_CATEGORY_MAP.items():
        if key.lower() in test_name.lower():
            return cat
    return "Other"


def extract_device_name(device: dict) -> str:
    return (
        device.get("decoded_name")
        or device.get("model")
        or device.get("name")
        or "Unknown device"
    )


def extract_pid_vid(device: dict) -> str:
    vid = device.get("vid")
    pid = device.get("pid")

    try:
        if vid is not None and pid is not None:
            return f"{int(vid):04X}:{int(pid):04X}"
    except Exception:
        pass

    return "—"


def extract_timestamp(raw: dict, fallback_path: Path) -> float:
    if "timestamp" in raw:
        try:
            return float(raw["timestamp"])
        except Exception:
            pass

    # fallback: filename timestamp
    m = re.search(r"_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})_", fallback_path.name)
    if m:
        dt = datetime.strptime(
            f"{m.group(1)} {m.group(2).replace('-', ':')}",
            "%Y-%m-%d %H:%M:%S",
        )
        return dt.timestamp()

    return fallback_path.stat().st_mtime


def format_date(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def load_journal_entries(journal_dir: Path) -> list[JournalEntry]:
    entries: list[JournalEntry] = []

    for path in journal_dir.glob("*.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        test_name = raw.get("test_name", "UnknownTest")
        device = raw.get("device", {})

        timestamp = extract_timestamp(raw, path)

        entry = JournalEntry(
            path=path,
            timestamp=timestamp,
            date=format_date(timestamp),
            test_name=test_name,
            category=infer_category(test_name),
            device_name=extract_device_name(device),
            pid_vid=extract_pid_vid(device),
            raw=raw,
        )

        entries.append(entry)

    # newest first by default
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return entries
