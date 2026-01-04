from collections import defaultdict, deque
from datetime import datetime
from threading import Lock

from PySide6.QtCore import QObject, Signal, QThread
import backend.modules.hwTests.keyboard.keyboardWindows as rawkbd
from time import strftime

from backend.modules.usbDecoder import decode_device_alternative


class KeyboardTestWorker(QObject):
    finished = Signal(dict)

    def __init__(self, vid, pid, duration=0):
        super().__init__()
        self.vid = vid
        self.pid = pid
        self.duration = duration
        self._running = True

        self.pressed_keys = set()
        self.heatmap = defaultdict(int)
        self.max_keys = 0
        self.total_presses = 0

        self.event_buffer = deque(maxlen=5000)
        self.buffer_lock = Lock()

    def stop(self):
        self._running = False

    def run(self):
        def on_event(event_type, scancode):
            if not self._running:
                return

            with self.buffer_lock:
                self.event_buffer.append((event_type, scancode))

            if event_type == "down":
                if scancode not in self.pressed_keys:
                    self.pressed_keys.add(scancode)
                    self.heatmap[scancode] += 1
                    self.total_presses += 1
                    self.max_keys = max(self.max_keys, len(self.pressed_keys))
            else:
                self.pressed_keys.discard(scancode)

        result = rawkbd.run_keyboard_test(
            self.vid,
            self.pid,
            duration=self.duration,
            event_callback=on_event,
            running_flag=lambda: self._running
        )

        result = {
            "test_name": "KeyboardMultiTest",
            "timestamp": datetime.now().isoformat(),
            "device": {
                "vid": self.vid,
                "pid": self.pid,
                "decoded_name": decode_device_alternative(self.vid, self.pid,),
            },
            "stats": {
                "total_presses": self.total_presses,
                "unique_keys": len(self.heatmap),
                "max_simultaneous": self.max_keys,
                "nkro_supported": self.max_keys >= 10,
            },
            "heatmap": dict(self.heatmap),
        }

        self.finished.emit(result)

    def pop_events(self, limit=100):
        events = []
        with self.buffer_lock:
            for _ in range(min(limit, len(self.event_buffer))):
                events.append(self.event_buffer.popleft())
        return events


    def get_stats(self):
        return {
            "pressed_now": len(self.pressed_keys),
            "max_simultaneous": self.max_keys,
            "unique_keys": len(self.heatmap),
            "total_presses": self.total_presses,
            "nkro": self.max_keys >= 10,
        }

    def get_heatmap(self):
        return dict(self.heatmap)
