# backend/modules/hwTests/mouse/mouse_service.py

from collections import defaultdict, deque
from threading import Lock
from datetime import datetime

from PySide6.QtCore import QObject, Signal
import backend.modules.hwTests.mouse.mouseIsolated as rawmouse
import math
import time


class MouseTestWorker(QObject):
    finished = Signal(dict)

    def __init__(self, vid, pid, duration=10):
        super().__init__()
        self.vid = vid
        self.pid = pid
        self.duration = duration
        self._running = True

        self.button_heatmap = defaultdict(int)
        self.movement_points = []
        self.jitter_samples = []
        self.packet_times = []

        self.event_buffer = deque(maxlen=5000)
        self.lock = Lock()

    def stop(self):
        self._running = False

    def _compute_polling_series(self, window_ms=100):
        times = self.packet_times
        if len(times) < 2:
            return []

        series = []
        window = window_ms / 1000.0

        start = times[0]
        i = 0

        while start < times[-1]:
            end = start + window
            count = 0

            while i < len(times) and times[i] < end:
                count += 1
                i += 1

            hz = count / window
            series.append((start - times[0], hz))
            start = end

        return series

    def _compute_jitter_series(self):
        times = self.packet_times
        if len(times) < 3:
            return []

        intervals = [
            times[i] - times[i - 1]
            for i in range(1, len(times))
        ]

        expected = sorted(intervals)[len(intervals) // 2]

        series = []
        t = times[1]

        for dt in intervals:
            jitter = abs(dt - expected)
            series.append((t - times[0], jitter * 1000))  # ms
            t += dt

        return series

    def run(self):
        def on_event(event_type, *data):
            if not self._running:
                return

            with self.lock:
                self.event_buffer.append((event_type, *data))

            if event_type == "button":
                self.button_heatmap[data[0]] += 1

            elif event_type == "wheel":
                self.button_heatmap[f"wheel_{data[0]}"] += 1

            elif event_type == "move":
                dx, dy = data
                self.movement_points.append((dx, dy))
                self.jitter_samples.append(math.hypot(dx, dy))

            elif event_type == "packet":
                self.packet_times.append(data[0])

        rawmouse.run_mouse_test(
            self.vid,
            self.pid,
            duration=self.duration,
            event_callback=on_event,
            running_flag=lambda: self._running
        )

        polling_rate = 0
        if len(self.packet_times) > 1:
            intervals = [
                self.packet_times[i] - self.packet_times[i - 1]
                for i in range(1, len(self.packet_times))
            ]
            avg_interval = sum(intervals) / len(intervals)
            polling_rate = round(1 / avg_interval)

        avg_jitter = (
            round(sum(self.jitter_samples) / len(self.jitter_samples), 4)
            if self.jitter_samples else 0
        )

        result = {
            "test_name": "MouseMultiTest",
            "timestamp": datetime.now().isoformat(),
            "device": {
                "vid": self.vid,
                "pid": self.pid,
            },
            "stats": {
                "polling_rate_hz": polling_rate,
                "avg_jitter": avg_jitter,
                "movement_samples": len(self.movement_points),
            },
            "graphs": {
                "polling_rate": self._compute_polling_series(),
                "jitter": self._compute_jitter_series(),
            },
            "button_heatmap": dict(self.button_heatmap),
            "raw_path": self.movement_points,
        }

        self.finished.emit(result)

    def pop_events(self, limit=100):
        events = []
        with self.lock:
            for _ in range(min(limit, len(self.event_buffer))):
                events.append(self.event_buffer.popleft())
        return events
