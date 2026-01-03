# backend/modules/hwTests/mouse/mouseIsolated.py

import win32gui
import ctypes
import time
import math

# ================= CONSTANTS =================

WM_INPUT = 0x00FF
RIDEV_INPUTSINK = 0x00000100
RIDEV_REMOVE = 0x00000001
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
RIDI_DEVICENAME = 0x20000007

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

wheel_v_accum = 0
wheel_h_accum = 0

# ================= STRUCT DEFINITIONS =================

class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", ctypes.c_ulong),
        ("dwSize", ctypes.c_ulong),
        ("hDevice", ctypes.c_void_p),
        ("wParam", ctypes.c_void_p),
    ]


class RAWMOUSE(ctypes.Structure):
    class _U(ctypes.Union):
        class _S(ctypes.Structure):
            _fields_ = [
                ("usButtonFlags", ctypes.c_ushort),
                ("usButtonData", ctypes.c_ushort),
            ]
        _fields_ = [
            ("ulButtons", ctypes.c_ulong),
            ("s", _S),
        ]
    _fields_ = [
        ("usFlags", ctypes.c_ushort),
        ("u", _U),
        ("ulRawButtons", ctypes.c_ulong),
        ("lLastX", ctypes.c_long),
        ("lLastY", ctypes.c_long),
        ("ulExtraInformation", ctypes.c_ulong),
    ]


class RAWINPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("mouse", RAWMOUSE)]
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("data", _U),
    ]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", ctypes.c_ushort),
        ("usUsage", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("hwndTarget", ctypes.c_void_p),
    ]

# ================= DEVICE FILTER =================

def device_matches_target(h_device):
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
    # HARD GUARD: never touch anything during shutdown
    if SHUTTING_DOWN:
        return 0

    if not INPUT_ACTIVE or EVENT_CALLBACK is None:
        return 0

    if msg != WM_INPUT:
        return 0

    size = ctypes.c_uint()
    ctypes.windll.user32.GetRawInputData(
        ctypes.c_void_p(lparam),
        RID_INPUT,
        None,
        ctypes.byref(size),
        ctypes.sizeof(RAWINPUTHEADER)
    )

    if size.value == 0:
        return 0

    buffer = ctypes.create_string_buffer(size.value)
    ctypes.windll.user32.GetRawInputData(
        ctypes.c_void_p(lparam),
        RID_INPUT,
        buffer,
        ctypes.byref(size),
        ctypes.sizeof(RAWINPUTHEADER)
    )

    raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT)).contents

    if raw.header.dwType != RIM_TYPEMOUSE:
        return 0

    if not device_matches_target(raw.header.hDevice):
        return 0

    now = time.time()
    EVENT_CALLBACK("packet", now)

    mouse = raw.data.mouse
    dx, dy = mouse.lLastX, mouse.lLastY

    if dx or dy:
        EVENT_CALLBACK("move", dx, dy)

    flags = mouse.u.s.usButtonFlags

    BUTTON_MAP = {
        0x0001: "left",
        0x0004: "right",
        0x0010: "middle",
        0x0040: "x1",
        0x0100: "x2",
    }

    for flag, name in BUTTON_MAP.items():
        if flags & flag:
            EVENT_CALLBACK("button", name)

    global wheel_v_accum, wheel_h_accum

    if flags & 0x0400:
        delta = ctypes.c_short(mouse.u.s.usButtonData).value
        wheel_v_accum += delta
        while abs(wheel_v_accum) >= 120:
            EVENT_CALLBACK("wheel", "up" if wheel_v_accum > 0 else "down")
            wheel_v_accum += -120 if wheel_v_accum > 0 else 120

    if flags & 0x0800:
        delta = ctypes.c_short(mouse.u.s.usButtonData).value
        wheel_h_accum += delta
        while abs(wheel_h_accum) >= 120:
            EVENT_CALLBACK("wheel", "right" if wheel_h_accum > 0 else "left")
            wheel_h_accum += -120 if wheel_h_accum > 0 else 120

    return 0


# 🔒 KEEP WNDPROC ALIVE FOR PROCESS LIFETIME
_proc_keepalive = WNDPROC(wnd_proc)

# ================= RAW INPUT REG =================

def register_mouse(hwnd):
    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,
        usUsage=0x02,
        dwFlags=RIDEV_INPUTSINK,
        hwndTarget=hwnd
    )
    ctypes.windll.user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(rid)
    )


def unregister_mouse():
    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,
        usUsage=0x02,
        dwFlags=RIDEV_REMOVE,
        hwndTarget=None
    )
    ctypes.windll.user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(rid)
    )

# ================= TEST RUNNER =================

def run_mouse_test(vid, pid, duration=0, event_callback=None, running_flag=None):
    global TARGET_VID, TARGET_PID, EVENT_CALLBACK, RUNNING_CHECK
    global INPUT_ACTIVE, SHUTTING_DOWN, wheel_v_accum, wheel_h_accum

    TARGET_VID = vid
    TARGET_PID = pid
    EVENT_CALLBACK = event_callback
    RUNNING_CHECK = running_flag

    wheel_v_accum = 0
    wheel_h_accum = 0

    INPUT_ACTIVE = True
    SHUTTING_DOWN = False

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _proc_keepalive
    wc.lpszClassName = "RawInputMouseTest"
    wc.hInstance = win32gui.GetModuleHandle(None)

    try:
        win32gui.RegisterClass(wc)
    except win32gui.error:
        pass

    hwnd = win32gui.CreateWindowEx(
        0, wc.lpszClassName, "HiddenRawInputMouseWindow",
        0, 0, 0, 0, 0,
        0, 0, wc.hInstance, None
    )

    register_mouse(hwnd)

    start = time.time()
    while True:
        if duration > 0 and time.time() - start >= duration:
            break
        if RUNNING_CHECK and not RUNNING_CHECK():
            break
        win32gui.PumpWaitingMessages()
        time.sleep(0.001)

    # ================= SAFE SHUTDOWN =================

    INPUT_ACTIVE = False
    SHUTTING_DOWN = True

    unregister_mouse()

    # Drain messages BEFORE destroy
    end = time.time() + 3.15
    while time.time() < end:
        win32gui.PumpWaitingMessages()
        time.sleep(0.001)

    win32gui.DestroyWindow(hwnd)

    EVENT_CALLBACK = None
    RUNNING_CHECK = None

    return {"duration_sec": duration}
