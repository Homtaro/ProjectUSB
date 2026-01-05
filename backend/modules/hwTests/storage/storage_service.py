# backend/modules/hwTests/storage/storage_service.py

import os
import shutil
import traceback
from statistics import mean

from PySide6.QtCore import QObject, Signal

from backend.modules.hwTests.storage.storageTestNoCache import (
    single_file_test,
    multi_file_test,
    get_device_info,
)
from backend.modules.hwTests.storage.storage_device_resolver import get_storage_device_from_path


# ==========================================================
# SINGLE FILE WORKER
# ==========================================================

class SingleFileStorageTestWorker(QObject):
    status = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        try:
            self.status.emit("Resolving device info…")
            info = get_device_info(self.path)

            if not self._running:
                return

            self.status.emit("Starting single-file test…")
            result = single_file_test(self.path)

            if not self._running:
                return

            device_info = get_storage_device_from_path(self.path)

            self.finished.emit({
                "test_name": "StorageSingleFileTest",
                "device": device_info,
                "drive": info,
                "result": result,
            })


        except Exception as e:
            self.error.emit(str(e))
            traceback.print_exc()


# ==========================================================
# MULTI FILE WORKER
# ==========================================================

class MultiFileStorageTestWorker(QObject):
    status = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        try:
            self.status.emit("Resolving device info…")
            info = get_device_info(self.path)

            if not self._running:
                return

            self.status.emit("Starting multi-file test…")
            results = multi_file_test(self.path)

            if not self._running:
                return

            # --- Aggregation ---
            write_speeds = [r["write_MBps"] for r in results]
            read_speeds = [r["read_MBps"] for r in results]
            ok_count = sum(1 for r in results if r["hash_match"])

            summary = {
                "avg_write_MBps": round(mean(write_speeds), 2),
                "avg_read_MBps": round(mean(read_speeds), 2),
                "files_ok": ok_count,
                "files_total": len(results),
            }

            device_info = get_storage_device_from_path(self.path)

            self.finished.emit({
                "test_name": "StorageMultiFileTest",
                "device": device_info,
                "drive": info,
                "summary": summary,
                "files": results,
            })


        except Exception as e:
            self.error.emit(str(e))
            traceback.print_exc()


# ==========================================================
# UTILS
# ==========================================================

def list_storage_paths():
    """
    Returns usable storage roots (Windows).
    """
    paths = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        root = f"{letter}:\\"
        if os.path.exists(root):
            try:
                shutil.disk_usage(root)
                paths.append(root)
            except Exception:
                pass
    return paths
