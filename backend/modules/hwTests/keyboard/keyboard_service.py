from collections import defaultdict

from PySide6.QtCore import QObject, Signal, QThread
import backend.modules.hwTests.keyboard.keyboardWindows as rawkbd
from time import strftime



class KeyboardTestWorker(QObject):
    key_down = Signal(int)
    key_up = Signal(int)
    stats_updated = Signal(dict)
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

    def stop(self):
        self._running = False

    def run(self):
        def on_event(event_type, scancode):
            if not self._running:
                return

            if event_type == "down":
                if scancode not in self.pressed_keys:
                    self.pressed_keys.add(scancode)
                    self.heatmap[scancode] += 1
                    self.total_presses += 1
                    self.max_keys = max(self.max_keys, len(self.pressed_keys))
                self.key_down.emit(scancode)

            elif event_type == "up":
                self.pressed_keys.discard(scancode)
                self.key_up.emit(scancode)

            self.stats_updated.emit({
                "pressed_now": len(self.pressed_keys),
                "max_simultaneous": self.max_keys,
                "unique_keys": len(self.heatmap),
                "total_presses": self.total_presses,
                "nkro": self.max_keys >= 10,
            })

        result = rawkbd.run_keyboard_test(
            self.vid,
            self.pid,
            duration=self.duration,
            event_callback=on_event,
            running_flag=lambda: self._running
        )

        self.finished.emit(result)

