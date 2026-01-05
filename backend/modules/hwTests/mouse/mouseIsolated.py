# backend/modules/hwTests/mouse/mouseIsolated.py

import win32gui
import win32con
import ctypes
import time
import uuid

# ================= CONSTANTS =================

WM_INPUT = 0x00FF
RIDEV_INPUTSINK = 0x00000100
RIDEV_REMOVE = 0x00000001
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
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

wheel_v_accum = 0
wheel_h_accum = 0

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
    try:
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
    except Exception:
        return False


# ================= WINDOW PROC =================

def wnd_proc(hwnd, msg, wparam, lparam):
    global wheel_v_accum, wheel_h_accum

    if SHUTTING_DOWN:
        return 0

    if not INPUT_ACTIVE:
        return 0

    if msg != WM_INPUT:
        return 0

    try:
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
        if EVENT_CALLBACK:
            try:
                EVENT_CALLBACK("packet", now)
            except Exception:
                pass

        mouse = raw.data.mouse
        dx, dy = mouse.lLastX, mouse.lLastY

        if dx or dy:
            if EVENT_CALLBACK:
                try:
                    EVENT_CALLBACK("move", dx, dy)
                except Exception:
                    pass

        flags = mouse.u.s.usButtonFlags

        BUTTON_MAP = {
            0x0001: "left",
            0x0004: "right",
            0x0010: "middle",
            0x0040: "x1",
            0x0100: "x2",
        }

        for flag, name in BUTTON_MAP.items():
            if flags & flag and EVENT_CALLBACK:
                try:
                    EVENT_CALLBACK("button", name)
                except Exception:
                    pass

        if flags & 0x0400:
            delta = ctypes.c_short(mouse.u.s.usButtonData).value
            wheel_v_accum += delta
            while abs(wheel_v_accum) >= 120:
                if EVENT_CALLBACK:
                    try:
                        EVENT_CALLBACK("wheel", "up" if wheel_v_accum > 0 else "down")
                    except Exception:
                        pass
                wheel_v_accum += -120 if wheel_v_accum > 0 else 120

        if flags & 0x0800:
            delta = ctypes.c_short(mouse.u.s.usButtonData).value
            wheel_h_accum += delta
            while abs(wheel_h_accum) >= 120:
                if EVENT_CALLBACK:
                    try:
                        EVENT_CALLBACK("wheel", "right" if wheel_h_accum > 0 else "left")
                    except Exception:
                        pass
                wheel_h_accum += -120 if wheel_h_accum > 0 else 120

    except Exception as e:
        # Silently ignore errors during shutdown
        if not SHUTTING_DOWN:
            print(f"Warning: wnd_proc error: {e}")
        return 0

    return 0


# ================= RAW INPUT REGISTRATION =================

def register_mouse(hwnd):
    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,
        usUsage=0x02,
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


def unregister_mouse():
    """Unregister raw input globally (not tied to specific hwnd)"""
    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,
        usUsage=0x02,
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

def run_mouse_test(vid, pid, duration=0, event_callback=None, running_flag=None):
    global TARGET_VID, TARGET_PID, EVENT_CALLBACK, RUNNING_CHECK
    global INPUT_ACTIVE, SHUTTING_DOWN, wheel_v_accum, wheel_h_accum
    global _proc_keepalive

    wheel_v_accum = 0
    wheel_h_accum = 0

    TARGET_VID = vid
    TARGET_PID = pid
    EVENT_CALLBACK = event_callback
    RUNNING_CHECK = running_flag

    INPUT_ACTIVE = False
    SHUTTING_DOWN = False

    if _proc_keepalive is None:
        _proc_keepalive = WNDPROC(wnd_proc)

    class_name = f"RawInputMouseTest_{uuid.uuid4().hex[:8]}"

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _proc_keepalive
    wc.lpszClassName = class_name
    wc.hInstance = win32gui.GetModuleHandle(None)

    try:
        class_atom = win32gui.RegisterClass(wc)
    except win32gui.error as e:
        print(f"Warning: RegisterClass failed: {e}")
        class_atom = None

    hwnd = win32gui.CreateWindowEx(
        0, class_name, "HiddenRawInputMouseWindow",
        0, 0, 0, 0, 0,
        0, 0, wc.hInstance, None
    )

    if not hwnd:
        print("Failed to create window")
        if class_atom:
            try:
                win32gui.UnregisterClass(class_name, wc.hInstance)
            except Exception:
                pass
        return {"duration_sec": 0}

    try:
        unregister_mouse()
        time.sleep(0.1)

        register_mouse(hwnd)

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
        # Cleanup sequence

        INPUT_ACTIVE = False
        EVENT_CALLBACK = None
        RUNNING_CHECK = None

        end = time.time() + 2.5
        while time.time() < end:
            win32gui.PumpWaitingMessages()
            time.sleep(0.001)

        SHUTTING_DOWN = True

        for _ in range(3000):
            win32gui.PumpWaitingMessages()
            time.sleep(0.001)

        try:
            unregister_mouse()
            time.sleep(0.05)
        except Exception as e:
            print(f"Warning: unregister_mouse failed: {e}")

        for _ in range(2000):
            win32gui.PumpWaitingMessages()
            time.sleep(0.001)

        try:
            win32gui.DestroyWindow(hwnd)
        except Exception as e:
            print(f"Warning: DestroyWindow failed: {e}")

        try:
            win32gui.UnregisterClass(class_name, wc.hInstance)
        except Exception as e:
            print(f"Warning: UnregisterClass failed: {e}")

        for _ in range(500):
            win32gui.PumpWaitingMessages()
            time.sleep(0.001)

        SHUTTING_DOWN = False

    return {"duration_sec": duration}