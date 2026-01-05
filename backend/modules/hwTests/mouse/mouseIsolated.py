import win32gui
import ctypes
import time
import uuid
from ctypes import wintypes

WM_INPUT = 0x00FF
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
RIDI_DEVICENAME = 0x20000007

if ctypes.sizeof(ctypes.c_void_p) == 8:
    LRESULT = ctypes.c_longlong
else:
    LRESULT = ctypes.c_long

WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

TARGET_VID = None
TARGET_PID = None
EVENT_CALLBACK = None
RUNNING_CHECK = None

INPUT_ACTIVE = False
SHUTTING_DOWN = False

wheel_v_accum = 0
wheel_h_accum = 0

_proc_keepalive = None
_hwnd = None
_class_name = None


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class RAWMOUSE(ctypes.Structure):
    class _U(ctypes.Union):
        class _S(ctypes.Structure):
            _fields_ = [
                ("usButtonFlags", wintypes.USHORT),
                ("usButtonData", wintypes.USHORT),
            ]
        _fields_ = [("ulButtons", wintypes.ULONG), ("s", _S)]

    _fields_ = [
        ("usFlags", wintypes.USHORT),
        ("u", _U),
        ("ulRawButtons", wintypes.ULONG),
        ("lLastX", wintypes.LONG),
        ("lLastY", wintypes.LONG),
        ("ulExtraInformation", wintypes.ULONG),
    ]


class RAWINPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("mouse", RAWMOUSE)]
    _fields_ = [("header", RAWINPUTHEADER), ("data", _U)]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


def device_matches_target(h_device):
    h_device = wintypes.HANDLE(h_device)  # <<< THIS IS THE FIX

    size = wintypes.UINT(0)
    if ctypes.windll.user32.GetRawInputDeviceInfoW(
        h_device, RIDI_DEVICENAME, None, ctypes.byref(size)
    ) == -1 or size.value == 0:
        return False

    buf = ctypes.create_unicode_buffer(size.value)
    if ctypes.windll.user32.GetRawInputDeviceInfoW(
        h_device, RIDI_DEVICENAME, buf, ctypes.byref(size)
    ) == -1:
        return False

    name = buf.value.lower()
    target = f"vid_{TARGET_VID:04x}&pid_{TARGET_PID:04x}"
    return target in name


def wnd_proc(hwnd, msg, wparam, lparam):
    global wheel_v_accum, wheel_h_accum

    if SHUTTING_DOWN or not INPUT_ACTIVE or msg != WM_INPUT:
        return 0

    cb = EVENT_CALLBACK
    if not cb:
        return 0

    size = wintypes.UINT(0)
    if ctypes.windll.user32.GetRawInputData(
        lparam, RID_INPUT, None, ctypes.byref(size),
        ctypes.sizeof(RAWINPUTHEADER)
    ) == -1:
        return 0

    buf = ctypes.create_string_buffer(size.value)
    if ctypes.windll.user32.GetRawInputData(
        lparam, RID_INPUT, buf, ctypes.byref(size),
        ctypes.sizeof(RAWINPUTHEADER)
    ) != size.value:
        return 0

    raw = ctypes.cast(buf, ctypes.POINTER(RAWINPUT)).contents
    if raw.header.dwType != RIM_TYPEMOUSE:
        return 0
    if not device_matches_target(raw.header.hDevice):
        return 0

    cb("packet", time.time())

    mouse = raw.data.mouse
    if mouse.lLastX or mouse.lLastY:
        cb("move", mouse.lLastX, mouse.lLastY)

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
            cb("button", name)

    if flags & 0x0400:
        delta = ctypes.c_short(mouse.u.s.usButtonData).value
        wheel_v_accum += delta
        while abs(wheel_v_accum) >= 120:
            cb("wheel", "up" if wheel_v_accum > 0 else "down")
            wheel_v_accum += -120 if wheel_v_accum > 0 else 120

    if flags & 0x0800:
        delta = ctypes.c_short(mouse.u.s.usButtonData).value
        wheel_h_accum += delta
        while abs(wheel_h_accum) >= 120:
            cb("wheel", "right" if wheel_h_accum > 0 else "left")
            wheel_h_accum += -120 if wheel_h_accum > 0 else 120

    return 0


def start_capture(vid, pid, event_callback, running_check):
    global TARGET_VID, TARGET_PID, EVENT_CALLBACK, RUNNING_CHECK
    global INPUT_ACTIVE, SHUTTING_DOWN, _proc_keepalive
    global _hwnd, _class_name

    TARGET_VID = vid
    TARGET_PID = pid
    EVENT_CALLBACK = event_callback
    RUNNING_CHECK = running_check

    if _proc_keepalive is None:
        _proc_keepalive = WNDPROC(wnd_proc)

    _class_name = f"RawInputMouse_{uuid.uuid4().hex[:6]}"
    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _proc_keepalive
    wc.lpszClassName = _class_name
    wc.hInstance = win32gui.GetModuleHandle(None)

    try:
        win32gui.RegisterClass(wc)
    except win32gui.error:
        pass

    _hwnd = win32gui.CreateWindowEx(
        0, _class_name, "RawInputHidden",
        0, 0, 0, 0, 0,
        0, 0, wc.hInstance, None
    )

    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,
        usUsage=0x02,
        dwFlags=RIDEV_INPUTSINK,
        hwndTarget=_hwnd,
    )
    ctypes.windll.user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(rid)
    )

    INPUT_ACTIVE = True
    SHUTTING_DOWN = False


def stop_capture():
    global INPUT_ACTIVE, SHUTTING_DOWN, EVENT_CALLBACK, RUNNING_CHECK
    global _hwnd, _class_name

    INPUT_ACTIVE = False
    SHUTTING_DOWN = True
    EVENT_CALLBACK = None
    RUNNING_CHECK = None

    if _hwnd:
        win32gui.DestroyWindow(_hwnd)
        _hwnd = None

    if _class_name:
        try:
            win32gui.UnregisterClass(_class_name, win32gui.GetModuleHandle(None))
        except Exception:
            pass
        _class_name = None
