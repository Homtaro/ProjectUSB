import sounddevice as sd
import numpy as np
import time

# ================= DEVICE UTILS =================

#def list_input_devices():
#    devices = sd.query_devices()
#    return [
#        (i, d["name"])
#        for i, d in enumerate(devices)
#        if d["max_input_channels"] > 0
#    ]

def list_input_devices():
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()

    wasapi_ids = {
        i for i, api in enumerate(hostapis)
        if "WASAPI" in api["name"]
    }

    result = []
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0 and d["hostapi"] in wasapi_ids:
            result.append((i, d["name"]))

    return result



def set_input_device(device_index):
    sd.default.device = (device_index, None)


# ================= RECORD / PLAYBACK =================

def record_audio(device_index, duration=5, samplerate=48000):
    set_input_device(device_index)

    print(f"Recording {duration}s...")
    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    return audio.squeeze()


def playback_audio(audio, samplerate=48000):
    print("Playing back recorded audio")
    sd.play(audio, samplerate)
    sd.wait()


# ================= ANALYSIS =================

def analyze_audio(audio):
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio ** 2)))

    return {
        "peak_level": round(peak, 4),
        "rms_level": round(rms, 4),
        "signal_present": peak > 0.01
    }


# ================= MAIN =================

if __name__ == "__main__":
    print("Available input devices:")
    for idx, name in list_input_devices():
        print(f"{idx}: {name}")

    device = int(input("\nSelect input device index: "))

    audio = record_audio(device, duration=5)
    stats = analyze_audio(audio)

    print("\n=== MICROPHONE ANALYSIS ===")
    for k, v in stats.items():
        print(f"{k}: {v}")

    playback_audio(audio)

    print("Audio input test complete")
