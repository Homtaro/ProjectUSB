import ctypes
import time
from ctypes import wintypes
from collections import defaultdict

# =============================
# TYPES / CONSTANTS
# =============================
HRESULT = ctypes.c_long  # define HRESULT since wintypes doesn't have it

dinput8 = ctypes.WinDLL("dinput8.dll")  # Use system dinput8.dll

DIRECTINPUT_VERSION = 0x0800
DIENUM_CONTINUE = 1
DIENUM_STOP = 0
DIEDFL_ATTACHEDONLY = 0x00000001
DI8DEVCLASS_GAMECTRL = 4

DISCL_BACKGROUND = 0x00000002
DISCL_NONEXCLUSIVE = 0x00000002

# =============================
# GUID DEFINITION
# =============================
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]

IID_IDirectInput8W = GUID(
    0xBF798031,
    0x483A,
    0x4DA2,
    (ctypes.c_ubyte * 8)(0xAA, 0x99, 0x5D, 0x64, 0xED, 0x36, 0x97, 0x00),
)

# =============================
# STRUCTS
# =============================
class DIDEVICEINSTANCEW(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("guidInstance", GUID),
        ("guidProduct", GUID),
        ("dwDevType", wintypes.DWORD),
        ("tszInstanceName", wintypes.WCHAR * 260),
        ("tszProductName", wintypes.WCHAR * 260),
        ("guidFFDriver", GUID),
        ("wUsagePage", wintypes.WORD),
        ("wUsage", wintypes.WORD),
    ]

class DIJOYSTATE2(ctypes.Structure):
    _fields_ = [
        ("lX", wintypes.LONG),
        ("lY", wintypes.LONG),
        ("lZ", wintypes.LONG),
        ("lRx", wintypes.LONG),
        ("lRy", wintypes.LONG),
        ("lRz", wintypes.LONG),
        ("rglSlider", wintypes.LONG * 2),
        ("rgdwPOV", wintypes.DWORD * 4),
        ("rgbButtons", wintypes.BYTE * 128),
    ]

class DIDATAFORMAT(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("dwObjSize", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("dwDataSize", wintypes.DWORD),
        ("dwNumObjs", wintypes.DWORD),
        ("rgodf", ctypes.c_void_p),
    ]

# =============================
# DirectInput8Create
# =============================
DirectInput8Create = dinput8.DirectInput8Create
DirectInput8Create.argtypes = [
    wintypes.HINSTANCE,
    wintypes.DWORD,
    ctypes.POINTER(GUID),
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_void_p,
]
DirectInput8Create.restype = HRESULT

# =============================
# CORE LOGIC
# =============================
def run_gamepad_test(duration=10):
    hinstance = ctypes.windll.kernel32.GetModuleHandleW(None)
    di = ctypes.c_void_p()

    hr = DirectInput8Create(
        hinstance,
        DIRECTINPUT_VERSION,
        ctypes.byref(IID_IDirectInput8W),
        ctypes.byref(di),
        None,
    )

    print(f"DirectInput init result: {hr}")

    if hr != 0:
        raise RuntimeError(f"DirectInput init failed (0x{hr & 0xffffffff:08X})")

    # Enumerate devices
    devices = []

    @ctypes.WINFUNCTYPE(
        wintypes.INT,
        ctypes.POINTER(DIDEVICEINSTANCEW),
        ctypes.c_void_p,
    )
    def enum_callback(instance, context):
        devices.append(instance.contents)
        return DIENUM_CONTINUE

    vtbl = ctypes.cast(di, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    EnumDevices = ctypes.CFUNCTYPE(
        HRESULT, wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD
    )(vtbl[4])

    hr = EnumDevices(di, DI8DEVCLASS_GAMECTRL, enum_callback, None, DIEDFL_ATTACHEDONLY)
    if not devices:
        raise RuntimeError("No DirectInput gamepad found")

    device_instance = devices[0]

    # CreateDevice
    CreateDevice = ctypes.CFUNCTYPE(
        HRESULT, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p
    )(vtbl[3])
    device = ctypes.c_void_p()
    hr = CreateDevice(di, ctypes.byref(device_instance.guidInstance), ctypes.byref(device), None)
    if hr != 0:
        raise RuntimeError(f"CreateDevice failed (0x{hr & 0xffffffff:08X})")

    dev_vtbl = ctypes.cast(device, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]

    # VTable function indices
    SetDataFormat = ctypes.CFUNCTYPE(HRESULT, ctypes.c_void_p)(dev_vtbl[11])
    SetCooperativeLevel = ctypes.CFUNCTYPE(HRESULT, wintypes.HWND, wintypes.DWORD)(dev_vtbl[13])
    Acquire = ctypes.CFUNCTYPE(HRESULT)(dev_vtbl[7])
    Poll = ctypes.CFUNCTYPE(HRESULT)(dev_vtbl[25])
    GetDeviceState = ctypes.CFUNCTYPE(HRESULT, wintypes.DWORD, ctypes.c_void_p)(dev_vtbl[9])

    # =============================
    # Define own DIDATAFORMAT for DIJOYSTATE2
    # =============================
    # This is minimal version for axes + 128 buttons
    c_dfDIJoystick2 = DIDATAFORMAT()
    c_dfDIJoystick2.dwSize = ctypes.sizeof(DIDATAFORMAT)
    c_dfDIJoystick2.dwObjSize = 0
    c_dfDIJoystick2.dwFlags = 0
    c_dfDIJoystick2.dwDataSize = ctypes.sizeof(DIJOYSTATE2)
    c_dfDIJoystick2.dwNumObjs = 0
    c_dfDIJoystick2.rgodf = None

    SetDataFormat(device, ctypes.byref(c_dfDIJoystick2))
    SetCooperativeLevel(device, None, DISCL_BACKGROUND | DISCL_NONEXCLUSIVE)
    Acquire(device)

    axes_samples = defaultdict(list)
    button_heatmap = defaultdict(int)
    state = DIJOYSTATE2()
    start = time.time()

    while time.time() - start < duration:
        Poll(device)
        if GetDeviceState(ctypes.sizeof(state), ctypes.byref(state)) == 0:
            axes_samples["LX"].append(state.lX)
            axes_samples["LY"].append(state.lY)
            axes_samples["RX"].append(state.lRx)
            axes_samples["RY"].append(state.lRy)
            for i, b in enumerate(state.rgbButtons):
                if b & 0x80:
                    button_heatmap[i] += 1
        time.sleep(0.005)

    return {
        "axes": axes_samples,
        "button_heatmap": dict(button_heatmap),
        "samples": len(axes_samples["LX"]),
    }

# =============================
# STANDALONE RUN
# =============================
if __name__ == "__main__":
    result = run_gamepad_test(duration=10)
    print("\n=== DIRECTINPUT GAMEPAD TEST ===")
    print(f"Samples collected: {result['samples']}")
    print(f"Buttons pressed: {len(result['button_heatmap'])}")
    for btn, count in result["button_heatmap"].items():
        print(f"  {btn}: {count}")
