
from collections import defaultdict, deque
from threading import Lock
from datetime import datetime

from PySide6.QtCore import QObject, Signal
import backend.modules.hwTests.mouse.mouseIsolated as rawmouse


class MouseTestWorker(QObject):
    finished = Signal(dict)

    def __init__(self, vid, pid, duration=10):
        super().__init__()

        self.vid = vid
        self.pid = pid
        self.duration = duration
        self._running = True

        # --- runtime buffers ---
        self.packet_times: list[float] = []
        self.button_heatmap = defaultdict(int)

        self.event_buffer = deque(maxlen=5000)
        self.lock = Lock()

    def stop(self):
        self._running = False

    # =========================
    # TRUE POLLING RATE SERIES
    # =========================
    def _compute_polling_series(self, window_ms=100):
        """
        Buckets packet timestamps into fixed windows.
        Output: [(t_sec, hz), ...]
        """
        times = self.packet_times
        if len(times) < 2:
            return []

        window = window_ms / 1000.0
        start_time = times[0]

        series = []
        i = 0
        bucket_start = start_time

        while bucket_start < times[-1]:
            bucket_end = bucket_start + window
            count = 0

            while i < len(times) and times[i] < bucket_end:
                count += 1
                i += 1

            hz = count / window
            series.append(
                (round(bucket_start - start_time, 3), round(hz, 2))
            )

            bucket_start = bucket_end

        return series

    # =========================
    # TRUE POLLING JITTER SERIES
    # =========================
    def _compute_jitter_series(self, bucket_ms=50):
        """
        Computes true polling jitter:
        jitter = |actual_interval - expected_interval|
        Then buckets jitter into time windows to reduce JSON size.
        """
        times = self.packet_times
        if len(times) < 3:
            return []

        # raw packet intervals
        intervals = [
            times[i] - times[i - 1]
            for i in range(1, len(times))
        ]

        # expected interval = median (robust)
        expected = sorted(intervals)[len(intervals) // 2]

        # compute raw jitter samples
        jitter_samples = [
            abs(dt - expected) * 1000.0  # ms
            for dt in intervals
        ]

        # timestamps for jitter samples
        jitter_times = times[1:]

        # bucket + average
        bucket = bucket_ms / 1000.0
        start = jitter_times[0]

        out = []
        acc = []
        bucket_start = start

        for t, j in zip(jitter_times, jitter_samples):
            if t - bucket_start <= bucket:
                acc.append(j)
            else:
                out.append((
                    round(bucket_start - start, 3),
                    round(sum(acc) / len(acc), 4)
                ))
                acc = [j]
                bucket_start = t

        if acc:
            out.append((
                round(bucket_start - start, 3),
                round(sum(acc) / len(acc), 4)
            ))

        return out

    # =========================
    # MAIN TEST RUN
    # =========================
    def run(self):
        def on_event(event_type, *data):
            if not self._running:
                return

            with self.lock:
                self.event_buffer.append((event_type, *data))

            if event_type == "packet":
                self.packet_times.append(data[0])

            elif event_type == "button":
                self.button_heatmap[data[0]] += 1

            elif event_type == "wheel":
                self.button_heatmap[f"wheel_{data[0]}"] += 1

        rawmouse.run_mouse_test(
            self.vid,
            self.pid,
            duration=self.duration,
            event_callback=on_event,
            running_flag=lambda: self._running
        )

        # --- summary stats ---
        polling_rate = 0
        if len(self.packet_times) > 1:
            intervals = [
                self.packet_times[i] - self.packet_times[i - 1]
                for i in range(1, len(self.packet_times))
            ]
            polling_rate = round(1 / (sum(intervals) / len(intervals)))

        jitter_series = self._compute_jitter_series()
        avg_jitter = (
            round(sum(v for _, v in jitter_series) / len(jitter_series), 4)
            if jitter_series else 0
        )

        result = {
            "test_name": "MouseMultiTest",
            "timestamp": datetime.now().isoformat(),
            "version": 2,

            "device": {
                "vid": self.vid,
                "pid": self.pid,
            },

            "config": {
                "duration_sec": self.duration,
                "polling_window_ms": 100,
                "jitter_bucket_ms": 50,
            },

            "stats": {
                "polling_rate_hz": polling_rate,
                "avg_jitter_ms": avg_jitter,
                "packet_count": len(self.packet_times),
            },

            "graphs": {
                "polling_rate": self._compute_polling_series(),
                "jitter": jitter_series,
            },

            "button_heatmap": dict(self.button_heatmap),
        }

        self.finished.emit(result)

    def pop_events(self, limit=100):
        events = []
        with self.lock:
            for _ in range(min(limit, len(self.event_buffer))):
                events.append(self.event_buffer.popleft())
        return events
