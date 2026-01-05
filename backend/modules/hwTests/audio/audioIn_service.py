import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

from backend.modules.hwTests.audio.audio_device_resolver import get_audio_device_info


class AudioInputTestWorker(QObject):
    recorded = Signal(np.ndarray)
    analyzed = Signal(dict)
    finished = Signal()
    error = Signal(str)

    def __init__(self, device_index: int, duration: int = 5, samplerate: int = 48000):
        super().__init__()
        self.device_index = device_index
        self.duration = duration
        self.samplerate = samplerate
        self._audio = None
        self.device_name = None
        self.device_info = None

    # ================= DEVICE =================

    @staticmethod
    def list_devices():
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        wasapi_ids = {i for i, api in enumerate(hostapis) if "WASAPI" in api["name"]}

        return [
            (i, d["name"])
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0 and d["hostapi"] in wasapi_ids
        ]

    # ================= ACTIONS =================

    def record(self):
        try:

            sd.default.device = (self.device_index, None)
            audio = sd.rec(
                int(self.duration * self.samplerate),
                samplerate=self.samplerate,
                channels=1,
                dtype="float32",
            )
            sd.wait()
            self._audio = audio.squeeze()
            self.recorded.emit(self._audio)
        except Exception as e:
            self.error.emit(str(e))

    def analyze(self):
        if self._audio is None:
            return

        devices = sd.query_devices()
        self.device_name = devices[self.device_index]["name"]
        self.device_info = get_audio_device_info(self.device_name)

        peak = float(np.max(np.abs(self._audio)))
        rms = float(np.sqrt(np.mean(self._audio ** 2)))

        self.analyzed.emit({
            "test_name": "AudioInputTest",
            "device": self.device_info or {
                "name": self.device_name,
                "vid": None,
                "pid": None,
            },
            "result": {
                "peak": round(peak, 4),
                "rms": round(rms, 4),
                "signal": peak > 0.01,
            }
        })

    def clone_for_playback(self):
        w = AudioInputTestWorker(self.device_index, self.duration, self.samplerate)
        w._audio = self._audio
        return w

    def playback(self):
        if self._audio is None:
            return

        sd.play(self._audio, self.samplerate)  # NON-BLOCKING


