import win32gui
import win32con
import ctypes
import time
from collections import defaultdict
import uuid

# ================= CONSTANTS =================

WM_INPUT = 0x00FF
RIDEV_INPUTSINK = 0x00000100
RIDEV_REMOVE = 0x00000001
RID_INPUT = 0x10000003
RIM_TYPEKEYBOARD = 1
RIDI_DEVICENAME = 0x20000007

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,  # LRESULT
    ctypes.c_void_p,  # HWND
    ctypes.c_uint,  # UINT
    ctypes.c_size_t,  # WPARAM
    ctypes.c_ssize_t  # LPARAM
)

# ================= GLOBAL STATE =================

TARGET_VID = None
TARGET_PID = None
EVENT_CALLBACK = None
RUNNING_CHECK = None

SHUTTING_DOWN = False
INPUT_ACTIVE = False

pressed_keys = set()
heatmap = defaultdict(int)
max_keys = 0

# KEEP CALLBACK ALIVE FOR PROCESS LIFETIME
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
    hdev = ctypes.c_void_p(h_device)

    size = ctypes.c_uint(0)
    ctypes.windll.user32.GetRawInputDeviceInfoW(
        hdev, RIDI_DEVICENAME, None, ctypes.byref(size)
    )
    if size.value == 0:
        return False

    buf = ctypes.create_unicode_buffer(size.value)
    ctypes.windll.user32.GetRawInputDeviceInfoW(
        hdev, RIDI_DEVICENAME, buf, ctypes.byref(size)
    )

    name = buf.value.lower()
    target = f"vid_{TARGET_VID:04x}&pid_{TARGET_PID:04x}".lower()
    return target in name


# ================= WINDOW PROC =================

def wnd_proc(hwnd, msg, wparam, lparam):
    global max_keys

    if SHUTTING_DOWN:
        return 0

    if not INPUT_ACTIVE:
        return 0

    if msg != WM_INPUT:
        return 0

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
        key_up = msg_type in (win32con.WM_KEYUP, win32con.WM_SYSKEYUP)

        flags = raw.keyboard.Flags
        make_code = raw.keyboard.MakeCode

        if flags & 0x04:  # RI_KEY_E1 (Pause/Break Sequence)
            if make_code == 0x1D:
                scancode = 0xE11D
            elif make_code == 0x45:
                return 0
            else:
                return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
        else:
            # Standard processing for non-E1 keys
            scancode = make_code
            if flags & 0x02:  # RI_KEY_E0
                scancode |= 0xE000

            if make_code == 0x45 and scancode == 0x45:
                return 0

        if scancode == 0:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        if key_down:
            if scancode not in pressed_keys:
                pressed_keys.add(scancode)
                heatmap[scancode] += 1
                if EVENT_CALLBACK:
                    EVENT_CALLBACK("down", scancode)

        elif key_up:
            pressed_keys.discard(scancode)
            if EVENT_CALLBACK:
                EVENT_CALLBACK("up", scancode)

        max_keys = max(max_keys, len(pressed_keys))

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


# ================= RAW INPUT REGISTRATION =================

def register_keyboard(hwnd):
    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,  # Generic Desktop
        usUsage=0x06,  # Keyboard
        dwFlags=RIDEV_INPUTSINK,
        hwndTarget=hwnd
    )

    result = ctypes.windll.user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(rid)
    )

    if not result:
        error_code = ctypes.get_last_error()
        print(f"RegisterRawInputDevices failed with error code: {error_code}")
        raise ctypes.WinError(error_code)


def unregister_keyboard():
    """Unregister raw input globally (not tied to specific hwnd)"""
    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,
        usUsage=0x06,
        dwFlags=RIDEV_REMOVE,
        hwndTarget=None
    )

    result = ctypes.windll.user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(rid)
    )

    if not result:
        error_code = ctypes.get_last_error()
        print(f"Warning: Unregister failed with error code: {error_code}")


# ================= TEST RUNNER =================

def run_keyboard_test(vid, pid, duration=0, event_callback=None, running_flag=None):
    global TARGET_VID, TARGET_PID
    global EVENT_CALLBACK, RUNNING_CHECK
    global INPUT_ACTIVE, SHUTTING_DOWN
    global _proc_keepalive, max_keys

    TARGET_VID = vid
    TARGET_PID = pid
    EVENT_CALLBACK = event_callback
    RUNNING_CHECK = running_flag

    pressed_keys.clear()
    heatmap.clear()
    max_keys = 0

    INPUT_ACTIVE = False  # Start disabled
    SHUTTING_DOWN = False

    # Create callback ONCE
    if _proc_keepalive is None:
        _proc_keepalive = WNDPROC(wnd_proc)

    # Use unique class name to avoid conflicts
    class_name = f"RawInputKeyboardTest_{uuid.uuid4().hex[:8]}"

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _proc_keepalive
    wc.lpszClassName = class_name
    wc.hInstance = win32gui.GetModuleHandle(None)

    try:
        class_atom = win32gui.RegisterClass(wc)
    except win32gui.error as e:
        print(f"Warning: RegisterClass failed: {e}")
        # Try to continue anyway
        class_atom = None

    hwnd = win32gui.CreateWindowEx(
        0, class_name, "HiddenRawInputKeyboardWindow",
        0, 0, 0, 0, 0,
        0, 0, wc.hInstance, None
    )

    if not hwnd:
        print("Failed to create window")
        if class_atom:
            win32gui.UnregisterClass(class_name, wc.hInstance)
        return {
            "duration_sec": 0,
            "max_simultaneous_keys": 0,
            "nkro_supported": False,
            "heatmap": {},
        }

    try:
        unregister_keyboard()
        time.sleep(0.1)  # Brief pause to ensure cleanup

        register_keyboard(hwnd)

        INPUT_ACTIVE = True

        start = time.time()
        while True:
            if duration > 0 and time.time() - start >= duration:
                break
            if RUNNING_CHECK and not RUNNING_CHECK():
                break

            win32gui.PumpWaitingMessages()
            time.sleep(0.001)

    finally:

        INPUT_ACTIVE = False
        EVENT_CALLBACK = None
        RUNNING_CHECK = None

        end = time.time() + 2.5
        while time.time() < end:
            win32gui.PumpWaitingMessages()
            time.sleep(0.001)

        SHUTTING_DOWN = True

        for _ in range(1000):
            win32gui.PumpWaitingMessages()
            time.sleep(0.001)

        unregister_keyboard()
        time.sleep(0.05)

        try:
            win32gui.DestroyWindow(hwnd)
        except Exception as e:
            print(f"Warning: DestroyWindow failed: {e}")

        try:
            win32gui.UnregisterClass(class_name, wc.hInstance)
        except Exception as e:
            print(f"Warning: UnregisterClass failed: {e}")

        for _ in range(1000):
            win32gui.PumpWaitingMessages()
            time.sleep(0.001)

        SHUTTING_DOWN = False

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