import sounddevice as sd
import numpy as np
import time


# ================= Global Values =================

SAFE_VOLUME = 0.10  # ~ -18 dBFS


# ================= DEVICE UTILS =================

def list_output_devices():
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()

    wasapi_ids = {
        i for i, api in enumerate(hostapis)
        if "WASAPI" in api["name"]
    }

    result = []
    for i, d in enumerate(devices):
        if d["max_output_channels"] > 0 and d["hostapi"] in wasapi_ids:
            result.append((i, d["name"], d["max_output_channels"]))

    return result


def set_output_device(device_index):
    sd.default.device = (None, device_index)


# ================= SIGNAL GENERATORS =================

def sine_sweep(duration=5.0, f_start=20, f_end=20000, samplerate=48000):
    t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)
    freqs = np.logspace(np.log10(f_start), np.log10(f_end), len(t))
    phase = 2 * np.pi * np.cumsum(freqs) / samplerate
    return np.sin(phase)


#def stereo_signal(left, right):
#    return np.column_stack((left, right))

def stereo_signal(left, right):
    return SAFE_VOLUME * np.column_stack((left, right))



# ================= TESTS =================

def play_sweep(device_index, duration=5):
    set_output_device(device_index)
    samplerate = 48000

    sweep = sine_sweep(duration=duration, samplerate=samplerate)
    silence = np.zeros_like(sweep)

    print("Playing LEFT channel sweep")
    sd.play(stereo_signal(sweep, silence), samplerate)
    sd.wait()

    time.sleep(0.5)

    print("Playing RIGHT channel sweep")
    sd.play(stereo_signal(silence, sweep), samplerate)
    sd.wait()


def play_channel_test(device_index):
    set_output_device(device_index)
    samplerate = 48000
    tone = np.sin(2 * np.pi * 440 * np.linspace(0, 1, samplerate))

    print("LEFT channel test (440 Hz)")
    sd.play(stereo_signal(tone, np.zeros_like(tone)), samplerate)
    sd.wait()

    time.sleep(0.5)

    print("RIGHT channel test (440 Hz)")
    sd.play(stereo_signal(np.zeros_like(tone), tone), samplerate)
    sd.wait()


# ================= MAIN =================

if __name__ == "__main__":
    print("Available output devices:")
    for idx, name, channels in list_output_devices():
        print(f"{idx}: {name} ({channels} ch)")

    device = int(input("\nSelect output device index: "))

    play_channel_test(device)
    play_sweep(device, duration=6)

    print("Audio output test complete")
