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

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint64, ctypes.c_int64)

# ================= GLOBAL STATE =================

pressed_keys = set()
heatmap = defaultdict(int)
unique_keys = set()
total_presses = 0
max_keys = 0
TARGET_DEVICE_HANDLE = None  # Will store the handle of the specific keyboard

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

# Move the callback wrapper to global scope to prevent Garbage Collection
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint64, ctypes.c_int64)
_proc_keepalive = None


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


# ================= DEVICE DISCOVERY =================

def get_device_handle(target_vid, target_pid):
    count = ctypes.c_uint(0)
    ctypes.windll.user32.GetRawInputDeviceList(None, ctypes.byref(count), ctypes.sizeof(RAWINPUTDEVICELIST))
    if count.value == 0:
        return None

    devices = (RAWINPUTDEVICELIST * count.value)()
    ctypes.windll.user32.GetRawInputDeviceList(devices, ctypes.byref(count), ctypes.sizeof(RAWINPUTDEVICELIST))

    target_str = f"vid_{target_vid:04x}&pid_{target_pid:04x}".lower()
    print(f"Searching for: {target_str}...")

    for i in range(count.value):
        h_device = devices[i].hDevice

        size = ctypes.c_uint(0)
        ctypes.windll.user32.GetRawInputDeviceInfoW(h_device, RIDI_DEVICENAME, None, ctypes.byref(size))
        if size.value == 0:
            continue

        name_buffer = ctypes.create_unicode_buffer(size.value)
        ctypes.windll.user32.GetRawInputDeviceInfoW(h_device, RIDI_DEVICENAME, name_buffer, ctypes.byref(size))
        device_name = name_buffer.value.lower()

        if target_str in device_name:
            print(f" -> FOUND MATCH: {device_name}")
            return h_device

    return None

# ================= WINDOW PROC =================

def wnd_proc(hwnd, msg, wparam, lparam):
    global max_keys
    global unique_keys, total_presses

    if msg == WM_INPUT:
        size = ctypes.c_uint()
        # Get size first
        ctypes.windll.user32.GetRawInputData(
            ctypes.c_void_p(lparam), RID_INPUT, None, ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER)
        )

        if size.value > 0:
            buffer = ctypes.create_string_buffer(size.value)
            ctypes.windll.user32.GetRawInputData(
                ctypes.c_void_p(lparam), RID_INPUT, buffer, ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER)
            )

            raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT)).contents

            if TARGET_DEVICE_HANDLE is not None:
                # Alternative: Compare device names if handle matching is unstable
                # because some keyboards use multiple handles for different keys.
                if raw.header.hDevice != TARGET_DEVICE_HANDLE:
                    # Get name of the device sending THIS message
                    #h_device = raw.header.hDevice
                    h_device = ctypes.c_void_p(raw.header.hDevice)
                    size_name = ctypes.c_uint(0)
                    ctypes.windll.user32.GetRawInputDeviceInfoW(h_device, RIDI_DEVICENAME, None,
                                                                ctypes.byref(size_name))

                    if size_name.value > 0:
                        name_buf = ctypes.create_unicode_buffer(size_name.value)
                        ctypes.windll.user32.GetRawInputDeviceInfoW(h_device, RIDI_DEVICENAME, name_buf,
                                                                    ctypes.byref(size_name))

                        # Verify if THIS handle belongs to the same VID/PID
                        target_id = f"vid_{0x258a:04x}&pid_{0x010c:04x}".lower()  # HARDCODING FOR NOW target VID/PID
                        if target_id not in name_buf.value.lower():
                            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
                    else:
                        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

            if raw.header.dwType != RIM_TYPEKEYBOARD:
                return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

            # Check for Keyboard type specifically
            if raw.header.dwType == RIM_TYPEKEYBOARD:
                msg_type = raw.keyboard.Message
                # Check for both standard and syskey versions
                key_down = msg_type in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN)
                key_up = msg_type in (win32con.WM_KEYUP, win32con.WM_SYSKEYUP)

                scancode = raw.keyboard.MakeCode
                E0 = 0x02
                if raw.keyboard.Flags & E0:
                    scancode |= 0xE000
                #if scancode == 0:
                #    scancode = raw.keyboard.VKey
                if scancode == 0:
                    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
                if key_down:
                    #pressed_keys.add(scancode)
                    #heatmap[scancode] += 1
                    #heatmap[(scancode, time.time())]
                    #heatmap[(scancode, time.time())] += 1
                    if scancode not in pressed_keys:  # prevents repeats while holding
                        pressed_keys.add(scancode)
                        unique_keys.add(scancode)
                        heatmap[scancode] += 1
                        total_presses += 1
                elif key_up:
                    pressed_keys.discard(scancode)

                max_keys = max(max_keys, len(pressed_keys))

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


# ================= REGISTER RAW INPUT =================

def register_keyboard(hwnd):
    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,
        usUsage=0x06,
        dwFlags=RIDEV_INPUTSINK,
        hwndTarget=hwnd,
    )

    if not ctypes.windll.user32.RegisterRawInputDevices(
            ctypes.byref(rid), 1, ctypes.sizeof(rid)
    ):
        raise ctypes.WinError()


# ================= TEST RUNNER =================

def run_keyboard_test(vid, pid, duration=10):
    global pressed_keys, heatmap, max_keys, TARGET_DEVICE_HANDLE, _proc_keepalive

    pressed_keys.clear()
    heatmap.clear()
    max_keys = 0

    TARGET_DEVICE_HANDLE = get_device_handle(vid, pid)

    # 1. Ensure the callback is preserved in memory
    _proc_keepalive = WNDPROC(wnd_proc)

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _proc_keepalive
    wc.lpszClassName = "RawInputKeyboardTest"
    wc.hInstance = win32gui.GetModuleHandle(None)

    try:
        win32gui.RegisterClass(wc)
    except Exception:
        pass  # Already registered

    # 2. Use a standard hidden window instead of HWND_MESSAGE
    # Some RawInput implementations prefer a real (but invisible) window
    hwnd = win32gui.CreateWindowEx(
        0, wc.lpszClassName, "HiddenKeyboardWindow",
        0, 0, 0, 0, 0,
        0, 0, wc.hInstance, None
    )

    register_keyboard(hwnd)

    print(f">>> Test running for {duration}s — Press keys on the TARGET keyboard!")
    start = time.time()

    while time.time() - start < duration:
        # 3. Use a more aggressive pump for the background sink
        win32gui.PumpWaitingMessages()
        time.sleep(0.01)

    win32gui.DestroyWindow(hwnd)
    _proc_keepalive = None
    TARGET_DEVICE_HANDLE = None

    return {
        "duration_sec": duration,
        "max_simultaneous_keys": max_keys,
        "nkro_supported": max_keys >= 10,
        "heatmap": dict(heatmap),
    }

# ================= MAIN =================

if __name__ == "__main__":
    # Replace with your keyboard VID/PID
    result = run_keyboard_test(0x258a, 0x010c, duration=10)

    print("\n=== TEST RESULT ===")
    print(f"Max simultaneous keys: {result['max_simultaneous_keys']}")
    print(f"NKRO supported: {result['nkro_supported']}")
    print(f"Unique keys pressed: {len(result['heatmap'])}")
    print(f"Total key presses: {sum(result['heatmap'].values())}")

    #Doesnt work since windows doesnt allow for easy device lock
    # Hidapi is far better, but requires Linux since windows blocks access
    # Use rawinput for now - keyboardWindows.py

    #Welp, it works now, kinda. Might be unstable with some keyboards using multiple handles
    #Plus, further testing is needed to ensure it works on all platforms
