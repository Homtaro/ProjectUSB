from PySide6.QtCore import QObject, Signal, QThread
import backend.modules.hwTests.keyboard.keyboardWindows as rawkbd


class KeyboardTestWorker(QObject):
    key_down = Signal(int)
    key_up = Signal(int)
    finished = Signal(dict)

    def __init__(self, vid, pid, duration=0):
        super().__init__()
        self.vid = vid
        self.pid = pid
        self.duration = duration
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        def on_event(event_type, scancode):
            if not self._running:
                return
            if event_type == "down":
                self.key_down.emit(scancode)
            elif event_type == "up":
                self.key_up.emit(scancode)

        result = rawkbd.run_keyboard_test(
            self.vid,
            self.pid,
            duration=self.duration,
            event_callback=on_event,
            running_flag=lambda: self._running
        )

        self.finished.emit(result)

