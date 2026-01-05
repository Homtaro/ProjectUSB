import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

SAFE_VOLUME = 0.10


class AudioOutputTestWorker(QObject):
    error = Signal(str)
    finished = Signal()

    def __init__(self, device_index: int, samplerate: int = 48000):
        super().__init__()
        self.device_index = device_index
        self.samplerate = samplerate

    # ================= DEVICE =================

    @staticmethod
    def list_devices():
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        wasapi_ids = {i for i, api in enumerate(hostapis) if "WASAPI" in api["name"]}

        return [
            (i, d["name"])
            for i, d in enumerate(devices)
            if d["max_output_channels"] > 0 and d["hostapi"] in wasapi_ids
        ]

    # ================= SIGNALS =================

    def _stereo(self, l, r):
        return SAFE_VOLUME * np.column_stack((l, r))

    def left_test(self):
        self._play_channel(left=True)

    def right_test(self):
        self._play_channel(left=False)

    def _play_channel(self, left=True):
        try:
            sd.default.device = (None, self.device_index)
            t = np.linspace(0, 1, self.samplerate, endpoint=False)
            tone = np.sin(2 * np.pi * 440 * t)

            if left:
                sd.play(self._stereo(tone, np.zeros_like(tone)), self.samplerate)
            else:
                sd.play(self._stereo(np.zeros_like(tone), tone), self.samplerate)

            sd.wait()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def sweep(self, duration=5):
        try:
            sd.default.device = (None, self.device_index)
            t = np.linspace(0, duration, int(self.samplerate * duration))
            freqs = np.logspace(np.log10(20), np.log10(20000), len(t))
            phase = 2 * np.pi * np.cumsum(freqs) / self.samplerate
            sweep = np.sin(phase)

            silence = np.zeros_like(sweep)
            sd.play(self._stereo(sweep, silence), self.samplerate)
            sd.wait()

            sd.play(self._stereo(silence, sweep), self.samplerate)
            sd.wait()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()
