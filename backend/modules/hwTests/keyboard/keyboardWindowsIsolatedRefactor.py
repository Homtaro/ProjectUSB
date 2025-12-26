import win32gui
import win32con
import ctypes
import time
from collections import defaultdict

# ================= CONSTANTS =================

WM_INPUT = 0x00FF
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RIM_TYPEKEYBOARD = 1
RIDI_DEVICENAME = 0x20000007

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong,
    ctypes.c_void_p,
    ctypes.c_uint,
    ctypes.c_uint64,
    ctypes.c_int64
)

# ================= GLOBAL STATE =================

pressed_keys = set()
heatmap = defaultdict(int)
max_keys = 0

TARGET_VID = None
TARGET_PID = None

# Keep callback alive (VERY IMPORTANT)
_proc_keepalive = None

# ================= STRUCT DEFINITIONS =================

class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", ctypes.c_ulong),
        ("dwSize", ctypes.c_ulong),
        ("hDevice", ctypes.c_void_p),
        ("wParam", ctypes.c_void_p),
    ]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", ctypes.c_ushort),
        ("Flags", ctypes.c_ushort),
        ("Reserved", ctypes.c_ushort),
        ("VKey", ctypes.c_ushort),
        ("Message", ctypes.c_uint),
        ("ExtraInformation", ctypes.c_ulong),
    ]


class RAWINPUT(ctypes.Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("keyboard", RAWKEYBOARD),
    ]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", ctypes.c_ushort),
        ("usUsage", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("hwndTarget", ctypes.c_void_p),
    ]


class RAWINPUTDEVICELIST(ctypes.Structure):
    _fields_ = [
        ("hDevice", ctypes.c_void_p),
        ("dwType", ctypes.c_ulong),
    ]


# ================= DEVICE UTIL =================

def device_matches_target(h_device):
    """
    Check whether this raw input device belongs to the target VID/PID.
    This is necessary because some keyboards expose multiple handles.
    """
    size = ctypes.c_uint(0)
    ctypes.windll.user32.GetRawInputDeviceInfoW(
        h_device, RIDI_DEVICENAME, None, ctypes.byref(size)
    )
    if size.value == 0:
        return False

    buf = ctypes.create_unicode_buffer(size.value)
    ctypes.windll.user32.GetRawInputDeviceInfoW(
        h_device, RIDI_DEVICENAME, buf, ctypes.byref(size)
    )

    name = buf.value.lower()
    target = f"vid_{TARGET_VID:04x}&pid_{TARGET_PID:04x}".lower()
    return target in name


# ================= WINDOW PROC =================

def wnd_proc(hwnd, msg, wparam, lparam):
    global max_keys

    if msg == WM_INPUT:
        size = ctypes.c_uint()

        ctypes.windll.user32.GetRawInputData(
            ctypes.c_void_p(lparam),
            RID_INPUT,
            None,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER)
        )

        if size.value == 0:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        buffer = ctypes.create_string_buffer(size.value)
        ctypes.windll.user32.GetRawInputData(
            ctypes.c_void_p(lparam),
            RID_INPUT,
            buffer,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER)
        )

        raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT)).contents

        if raw.header.dwType != RIM_TYPEKEYBOARD:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        # Filter by VID/PID
        if not device_matches_target(raw.header.hDevice):
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        msg_type = raw.keyboard.Message
        key_down = msg_type in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN)
        key_up   = msg_type in (win32con.WM_KEYUP,   win32con.WM_SYSKEYUP)

        scancode = raw.keyboard.MakeCode

        # Handle extended keys
        if raw.keyboard.Flags & 0x02:  # RI_KEY_E0
            scancode |= 0xE000

        if scancode == 0:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        if key_down:
            if scancode not in pressed_keys:
                pressed_keys.add(scancode)
                heatmap[scancode] += 1
        elif key_up:
            pressed_keys.discard(scancode)

        max_keys = max(max_keys, len(pressed_keys))

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


# ================= RAW INPUT REGISTRATION =================

def register_keyboard(hwnd):
    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,   # Generic Desktop
        usUsage=0x06,       # Keyboard
        dwFlags=RIDEV_INPUTSINK,
        hwndTarget=hwnd
    )

    if not ctypes.windll.user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(rid)
    ):
        raise ctypes.WinError()


# ================= TEST RUNNER =================

def run_keyboard_test(vid, pid, duration=10):
    global pressed_keys, heatmap, max_keys
    global TARGET_VID, TARGET_PID, _proc_keepalive

    TARGET_VID = vid
    TARGET_PID = pid

    pressed_keys.clear()
    heatmap.clear()
    max_keys = 0

    _proc_keepalive = WNDPROC(wnd_proc)

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _proc_keepalive
    wc.lpszClassName = "RawInputKeyboardTest"
    wc.hInstance = win32gui.GetModuleHandle(None)

    try:
        win32gui.RegisterClass(wc)
    except win32gui.error:
        pass

    hwnd = win32gui.CreateWindowEx(
        0,
        wc.lpszClassName,
        "HiddenRawInputWindow",
        0,
        0, 0, 0, 0,
        0, 0,
        wc.hInstance,
        None
    )

    register_keyboard(hwnd)

    print(f">>> Testing keyboard VID={vid:04x} PID={pid:04x} for {duration}s")

    start = time.time()
    while time.time() - start < duration:
        win32gui.PumpWaitingMessages()
        time.sleep(0.01)

    win32gui.DestroyWindow(hwnd)
    _proc_keepalive = None

    return {
        "duration_sec": duration,
        "max_simultaneous_keys": max_keys,
        "nkro_supported": max_keys >= 10,
        "heatmap": dict(heatmap),
    }


# ================= MAIN =================

if __name__ == "__main__":
    # device vendor and product ID
    VID = 0x258A
    PID = 0x010C

    result = run_keyboard_test(VID, PID, duration=10)

    print("\n=== TEST RESULT ===")
    print(f"Max simultaneous keys: {result['max_simultaneous_keys']}")
    print(f"NKRO supported: {result['nkro_supported']}")
    print(f"Unique keys pressed: {len(result['heatmap'])}")
    print(f"Total key presses: {sum(result['heatmap'].values())}")
