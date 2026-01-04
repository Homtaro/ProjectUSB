import time
import math
from collections import defaultdict

from PySide6.QtCore import QObject, Signal

from backend.modules.hwTests.gamepad.gamepadXIsolated import (
    read_xinput_state,
    detect_active_controllers,
)


class GamepadTestWorker(QObject):
    """
    XInput Gamepad test worker (LIVE, infinite).
    WMI / VID-PID resolution MUST be done outside this worker.
    """

    # ---------- Signals ----------
    live = Signal(dict)        # emitted ~60 Hz
    stats = Signal(dict)       # emitted ~1 Hz
    finished = Signal(dict)
    error = Signal(str)

    def __init__(
        self,
        controller_index: int | None = None,
        device_info: dict | None = None,   # <- injected, NOT resolved here
    ):
        super().__init__()

        self.controller_index = controller_index
        self._device_info = device_info or {}

        self._running = False

        # ---------- Stats ----------
        self._last_packet = None
        self._packet_times: list[float] = []

        self._left_radii: list[float] = []
        self._right_radii: list[float] = []

        self._button_heatmap = defaultdict(int)
        self._last_buttons: dict[str, float] = {}

    # ==========================================================
    # CONTROL
    # ==========================================================

    def stop(self):
        self._running = False

    def reset_stats(self):
        self._packet_times.clear()
        self._left_radii.clear()
        self._right_radii.clear()
        self._button_heatmap.clear()
        self._last_buttons.clear()
        self._last_packet = None

    # ==========================================================
    # MAIN LOOP
    # ==========================================================

    def run(self):
        try:
            # ---------- Select controller ----------
            if self.controller_index is None:
                active = detect_active_controllers()
                if not active:
                    self.error.emit("No XInput controllers detected")
                    return
                self.controller_index = active[0]  # constraint accepted

            self._running = True
            last_stats_emit = 0.0

            # ---------- Poll loop ----------
            while self._running:
                state = read_xinput_state(self.controller_index)
                if not state:
                    time.sleep(0.01)
                    continue

                # ================= LIVE UPDATE =================
                self.live.emit(state)

                # ================= POLLING RATE =================
                packet = state["packet"]
                now = time.time()
                if packet != self._last_packet:
                    self._packet_times.append(now)
                    self._last_packet = packet

                # ================= BUTTON HEATMAP =================
                for btn, val in state["buttons"].items():
                    prev = self._last_buttons.get(btn, 0.0)
                    if val > 0 and prev == 0:
                        self._button_heatmap[btn] += 1
                    self._last_buttons[btn] = val

                # ================= STICK QUALITY =================
                lx, ly = state["sticks"]["L"]
                rx, ry = state["sticks"]["R"]

                # RAW magnitudes — DO NOT CLAMP
                l_mag = math.hypot(lx, ly)
                r_mag = math.hypot(rx, ry)

                # keep meaningful outer samples only
                if 0.85 < l_mag < 1.25:
                    self._left_radii.append(l_mag)

                if 0.85 < r_mag < 1.25:
                    self._right_radii.append(r_mag)

                # ================= STATS EMIT =================
                if time.time() - last_stats_emit > 1.0:
                    self.stats.emit(self._build_result()["stats"])
                    last_stats_emit = time.time()

                time.sleep(0.016)  # ~60 Hz

            # ---------- Final snapshot ----------
            self.finished.emit(self._build_result())

        except Exception as e:
            self.error.emit(str(e))

    # ==========================================================
    # RESULT BUILDING
    # ==========================================================

    def _build_result(self) -> dict:
        def analyze(radii: list[float]) -> dict:
            if not radii:
                return {}

            IDEAL = 1.0
            errors = [abs(r - IDEAL) for r in radii]

            return {
                "max_radius": round(max(radii), 3),
                "mean_radius": round(sum(radii) / len(radii), 3),
                "circular_error": round(sum(errors) / len(errors), 4),
                "circular_error_pct": round(
                    (sum(errors) / len(errors)) * 100, 2
                ),
            }

        polling = 0
        if len(self._packet_times) > 1:
            intervals = [
                self._packet_times[i] - self._packet_times[i - 1]
                for i in range(1, len(self._packet_times))
            ]
            polling = round(1 / (sum(intervals) / len(intervals)))

        return {
            "test_name": "GamepadMultiTest",
            "timestamp": time.time(),
            "device": {
                "type": "xinput",
                "controller_index": self.controller_index,
                **self._device_info,
            },
            "stats": {
                "polling_rate_hz": polling,
                "left_stick": analyze(self._left_radii),
                "right_stick": analyze(self._right_radii),
            },
            "button_heatmap": dict(self._button_heatmap),
        }
