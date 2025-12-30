import ctypes
import os
import time
import math
from collections import defaultdict

# ================= PATH RESOLUTION =================

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DINPUT_DLL_PATH = os.path.abspath(
#     os.path.join(BASE_DIR, "..", "..", "..", "dlls", "dinput8.dll")
# )
#
# if not os.path.exists(DINPUT_DLL_PATH):
#     raise FileNotFoundError(f"dinput8.dll not found at {DINPUT_DLL_PATH}")

#dinput8 = ctypes.WinDLL(DINPUT_DLL_PATH)

dinput8 = ctypes.WinDLL("dinput8.dll")

# ================= GUID =================

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


IID_IDirectInput8A = GUID(
    0xBF798030,
    0x483A,
    0x4DA2,
    (ctypes.c_ubyte * 8)(0xAA, 0x99, 0x5D, 0x64, 0xED, 0x36, 0x97, 0x00)
)

# Define the IDirectInput8Vtbl to correctly map method offsets
class IDirectInput8AVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.c_void_p),
        ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p),
        ("CreateDevice", ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)),
        ("EnumDevices", ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong)),
        # ... other methods omitted for brevity, but order matters
    ]

class IDirectInput8A(ctypes.Structure):
    _fields_ = [("lpVtbl", ctypes.POINTER(IDirectInput8AVtbl))]

# Define argtypes for DirectInput8Create to ensure pointers are handled correctly
dinput8.DirectInput8Create.argtypes = [
    ctypes.c_void_p,  # hinst
    ctypes.c_ulong,   # dwVersion
    ctypes.POINTER(GUID),  # riid
    ctypes.POINTER(ctypes.c_void_p),  # ppvOut
    ctypes.c_void_p   # punkOuter
]
dinput8.DirectInput8Create.restype = ctypes.c_long

# ================= CONSTANTS =================

DIRECTINPUT_VERSION = 0x0800
DI8DEVCLASS_GAMECTRL = 4
DIEDFL_ATTACHEDONLY = 0x00000001


# ================= STRUCTS =================

MAX_AXES = 8
MAX_BUTTONS = 128

class DIJOYSTATE2(ctypes.Structure):
    _fields_ = [
        ("lX", ctypes.c_long),
        ("lY", ctypes.c_long),
        ("lZ", ctypes.c_long),
        ("lRx", ctypes.c_long),
        ("lRy", ctypes.c_long),
        ("lRz", ctypes.c_long),
        ("rglSlider", ctypes.c_long * 2),
        ("rgdwPOV", ctypes.c_ulong * 4),
        ("rgbButtons", ctypes.c_ubyte * MAX_BUTTONS),
    ]


class DIDEVICEINSTANCE(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.c_ulong),
        ("guidInstance", GUID),
        ("guidProduct", GUID),
        ("dwDevType", ctypes.c_ulong),
        ("tszInstanceName", ctypes.c_char * 260),
        ("tszProductName", ctypes.c_char * 260),
        ("guidFFDriver", GUID),
        ("wUsagePage", ctypes.c_ushort),
        ("wUsage", ctypes.c_ushort),
    ]


LPDIENUMDEVICESCALLBACK = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    ctypes.POINTER(DIDEVICEINSTANCE),
    ctypes.c_void_p
)

# ================= GLOBAL STATE =================

TARGET_VID = None
TARGET_PID = None

button_heatmap = defaultdict(int)
axis_samples = defaultdict(list)
packet_times = []

# ================= UTIL =================

def guid_to_vid_pid(guid):
    vid = guid.Data1 & 0xFFFF
    pid = (guid.Data1 >> 16) & 0xFFFF
    return vid, pid

# ================= DEVICE ENUM =================

def find_device(di):
    found = ctypes.c_void_p()

    @LPDIENUMDEVICESCALLBACK
    def callback(instance, context):
        nonlocal found

        vid, pid = guid_to_vid_pid(instance.contents.guidProduct)
        if vid == TARGET_VID and pid == TARGET_PID:
            hr = di.contents.CreateDevice(
                ctypes.byref(instance.contents.guidInstance),
                ctypes.byref(found),
                None
            )
            return 0  # stop enum

        return 1  # continue

    di.contents.EnumDevices(
        DI8DEVCLASS_GAMECTRL,
        callback,
        None,
        DIEDFL_ATTACHEDONLY
    )

    return found

# ================= TEST RUNNER =================

def run_gamepad_test(vid, pid, duration=10):
    global TARGET_VID, TARGET_PID

    TARGET_VID = vid
    TARGET_PID = pid

    button_heatmap.clear()
    axis_samples.clear()
    packet_times.clear()

    di_ptr = ctypes.c_void_p()
    # Get instance handle explicitly
    hinst = ctypes.windll.kernel32.GetModuleHandleW(None)

    # Use pointer(IID) instead of byref to be more explicit for the DLL call
    hr = dinput8.DirectInput8Create(
        hinst,
        DIRECTINPUT_VERSION,
        ctypes.byref(IID_IDirectInput8A),
        ctypes.byref(di_ptr),
        None
    )

    if hr != 0:
        raise RuntimeError(f"DirectInput init failed (0x{hr & 0xffffffff:08X})")

    di = ctypes.cast(di_ptr, ctypes.POINTER(IDirectInput8A))


    device = find_device(di)
    if not device:
        raise RuntimeError("Target gamepad not found")

    device = ctypes.cast(device, ctypes.POINTER(ctypes.c_void_p))

    device.contents.SetDataFormat(ctypes.byref(ctypes.c_void_p()))  # default
    device.contents.Acquire()

    js = DIJOYSTATE2()

    start = time.time()
    while time.time() - start < duration:
        device.contents.Poll()
        if device.contents.GetDeviceState(ctypes.sizeof(js), ctypes.byref(js)) == 0:
            now = time.time()
            packet_times.append(now)

            # Axes
            for name, value in {
                "lx": js.lX,
                "ly": js.lY,
                "lz": js.lZ,
                "rx": js.lRx,
                "ry": js.lRy,
                "rz": js.lRz,
            }.items():
                axis_samples[name].append(value)

            # Buttons
            for i, state in enumerate(js.rgbButtons):
                if state & 0x80:
                    button_heatmap[f"button_{i}"] += 1

        time.sleep(0.001)

    device.contents.Unacquire()

    # ================= ANALYSIS =================

    polling_rate = 0
    if len(packet_times) > 1:
        intervals = [
            packet_times[i] - packet_times[i - 1]
            for i in range(1, len(packet_times))
        ]
        polling_rate = round(1 / (sum(intervals) / len(intervals)))

    axes = {}
    for name, samples in axis_samples.items():
        if not samples:
            continue
        axes[name] = {
            "min": min(samples),
            "max": max(samples),
            "avg": round(sum(samples) / len(samples), 2),
            "drift": round(sum(abs(x) for x in samples) / len(samples), 2),
        }

    return {
        "duration_sec": duration,
        "polling_rate_hz": polling_rate,
        "buttons": dict(button_heatmap),
        "axes": axes,
    }

# ================= MAIN =================

if __name__ == "__main__":
    VID = 0x054C  # example: Sony
    PID = 0x09CC  # DualShock 4

    result = run_gamepad_test(VID, PID, duration=10)

    print("\n=== DIRECTINPUT GAMEPAD TEST RESULT ===")
    print(f"Polling rate: {result['polling_rate_hz']} Hz\n")

    print("Buttons:")
    for b, c in result["buttons"].items():
        print(f"  {b:10}: {c}")

    print("\nAxes:")
    for a, v in result["axes"].items():
        print(f"  {a}: {v}")
