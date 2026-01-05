import win32gui
import win32con
import ctypes
import time
import uuid
from collections import defaultdict
from ctypes import wintypes

# ================= CONSTANTS =================

WM_INPUT = 0x00FF
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RIM_TYPEKEYBOARD = 1
RIDI_DEVICENAME = 0x20000007

# ================= LRESULT =================

if ctypes.sizeof(ctypes.c_void_p) == 8:
    LRESULT = ctypes.c_longlong
else:
    LRESULT = ctypes.c_long

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,   # LRESULT
    ctypes.c_void_p,    # HWND
    ctypes.c_uint,      # UINT
    ctypes.c_size_t,    # WPARAM
    ctypes.c_ssize_t    # LPARAM
)



# ================= GLOBAL STATE =================

TARGET_VID = None
TARGET_PID = None
EVENT_CALLBACK = None
RUNNING_CHECK = None

INPUT_ACTIVE = False
SHUTTING_DOWN = False

pressed_keys = set()
heatmap = defaultdict(int)

_proc_keepalive = None
_hwnd = None

# ================= STRUCTS =================

class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", wintypes.USHORT),
        ("Flags", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("VKey", wintypes.USHORT),
        ("Message", wintypes.UINT),
        ("ExtraInformation", wintypes.ULONG),
    ]


class RAWINPUT(ctypes.Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("keyboard", RAWKEYBOARD),
    ]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


# ================= DEVICE FILTER =================

def device_matches_target(h_device):
    hdev = wintypes.HANDLE(h_device)   # <<< THIS IS THE FIX

    size = wintypes.UINT(0)
    if ctypes.windll.user32.GetRawInputDeviceInfoW(
        hdev, RIDI_DEVICENAME, None, ctypes.byref(size)
    ) == -1 or size.value == 0:
        return False

    buf = ctypes.create_unicode_buffer(size.value)
    if ctypes.windll.user32.GetRawInputDeviceInfoW(
        hdev, RIDI_DEVICENAME, buf, ctypes.byref(size)
    ) == -1:
        return False

    name = buf.value.lower()
    target = f"vid_{TARGET_VID:04x}&pid_{TARGET_PID:04x}".lower()
    return target in name



# ================= WNDPROC =================

def wnd_proc(hwnd, msg, wparam, lparam):
    if SHUTTING_DOWN or not INPUT_ACTIVE or msg != WM_INPUT:
        return 0

    cb = EVENT_CALLBACK
    if not cb:
        return 0

    size = wintypes.UINT(0)

    if ctypes.windll.user32.GetRawInputData(
        lparam,
        RID_INPUT,
        None,
        ctypes.byref(size),
        ctypes.sizeof(RAWINPUTHEADER),
    ) == -1:
        return 0

    buffer = ctypes.create_string_buffer(size.value)

    if ctypes.windll.user32.GetRawInputData(
        lparam,
        RID_INPUT,
        buffer,
        ctypes.byref(size),
        ctypes.sizeof(RAWINPUTHEADER),
    ) != size.value:
        return 0

    raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT)).contents

    if raw.header.dwType != RIM_TYPEKEYBOARD:
        return 0

    if not device_matches_target(raw.header.hDevice):
        return 0

    msg_type = raw.keyboard.Message
    key_down = msg_type in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN)
    key_up = msg_type in (win32con.WM_KEYUP, win32con.WM_SYSKEYUP)

    flags = raw.keyboard.Flags
    make_code = raw.keyboard.MakeCode

    # ----- E1 (Pause / Break) -----
    if flags & 0x04:
        if make_code == 0x1D:
            scancode = 0xE11D
        elif make_code == 0x45:
            return 0
        else:
            return 0

    # ----- Normal keys -----
    else:
        scancode = make_code
        if flags & 0x02:
            scancode |= 0xE000

        # NumLock fake
        if make_code == 0x45 and scancode == 0x45:
            return 0

    # ----- Print Screen fake shift -----
    if scancode in (0xE02A, 0xE0AA):
        return 0

    if scancode == 0:
        return 0

    if key_down:
        if scancode not in pressed_keys:
            pressed_keys.add(scancode)
            heatmap[scancode] += 1
            cb("down", scancode)
    elif key_up:
        pressed_keys.discard(scancode)
        cb("up", scancode)

    return 0


# ================= CONTROL API (MAIN THREAD ONLY) =================

def start_capture(vid, pid, event_callback, running_check):
    global TARGET_VID, TARGET_PID, EVENT_CALLBACK, RUNNING_CHECK
    global INPUT_ACTIVE, SHUTTING_DOWN, _proc_keepalive, _hwnd

    TARGET_VID = vid
    TARGET_PID = pid
    EVENT_CALLBACK = event_callback
    RUNNING_CHECK = running_check

    pressed_keys.clear()
    heatmap.clear()

    if _proc_keepalive is None:
        _proc_keepalive = WNDPROC(wnd_proc)

    class_name = f"RawInputKeyboard_{uuid.uuid4().hex[:6]}"
    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _proc_keepalive
    wc.lpszClassName = class_name
    wc.hInstance = win32gui.GetModuleHandle(None)

    try:
        win32gui.RegisterClass(wc)
    except win32gui.error:
        pass

    _hwnd = win32gui.CreateWindowEx(
        0, class_name, "RawKeyboardHidden",
        0, 0, 0, 0, 0,
        0, 0, wc.hInstance, None
    )

    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,
        usUsage=0x06,
        dwFlags=RIDEV_INPUTSINK,
        hwndTarget=_hwnd
    )

    ctypes.windll.user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(rid)
    )

    INPUT_ACTIVE = True
    SHUTTING_DOWN = False


def stop_capture():
    global INPUT_ACTIVE, SHUTTING_DOWN, EVENT_CALLBACK, RUNNING_CHECK, _hwnd

    INPUT_ACTIVE = False
    SHUTTING_DOWN = True
    EVENT_CALLBACK = None
    RUNNING_CHECK = None

    if _hwnd:
        win32gui.DestroyWindow(_hwnd)
        _hwnd = None
