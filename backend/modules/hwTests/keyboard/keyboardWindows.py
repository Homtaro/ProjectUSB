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

# ================= GLOBAL STATE =================

pressed_keys = set()
heatmap = defaultdict(int)
max_keys = 0

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

# ================= WINDOW PROC =================

def wnd_proc(hwnd, msg, wparam, lparam):
    global max_keys

    if msg == WM_INPUT:
        size = ctypes.c_uint(0)

        res = ctypes.windll.user32.GetRawInputData(
            lparam,
            RID_INPUT,
            None,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER),
        )

        if res != 0 or size.value == 0:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        buffer = ctypes.create_string_buffer(size.value)

        ctypes.windll.user32.GetRawInputData(
            lparam,
            RID_INPUT,
            buffer,
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER),
        )

        raw = RAWINPUT.from_buffer(buffer)

        if raw.header.dwType != RIM_TYPEKEYBOARD:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        key_down = raw.keyboard.Message in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN)
        scancode = raw.keyboard.MakeCode

        if key_down:
            pressed_keys.add(scancode)
            heatmap[scancode] += 1
        else:
            pressed_keys.discard(scancode)

        max_keys = max(max_keys, len(pressed_keys))

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

# ================= REGISTER RAW INPUT =================

def register_keyboard(hwnd):
    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,
        usUsage=0x06,  # Keyboard
        dwFlags=RIDEV_INPUTSINK,
        hwndTarget=hwnd,
    )

    if not ctypes.windll.user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(rid)
    ):
        raise ctypes.WinError()

# ================= TEST RUNNER =================

def run_keyboard_test(duration=10):
    global pressed_keys, heatmap, max_keys

    pressed_keys.clear()
    heatmap.clear()
    max_keys = 0

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = wnd_proc
    wc.lpszClassName = "RawInputKeyboardTest"

    hinst = win32gui.GetModuleHandle(None)
    class_atom = win32gui.RegisterClass(wc)

    hwnd = win32gui.CreateWindowEx(
        0,
        class_atom,
        "HiddenKeyboardWindow",
        0,
        0, 0, 0, 0,
        win32con.HWND_MESSAGE,
        0,
        hinst,
        None,
    )

    register_keyboard(hwnd)

    print(">>> Keyboard test running — press keys NOW!")
    start = time.time()

    while time.time() - start < duration:
        win32gui.PumpWaitingMessages()
        time.sleep(0.001)

    win32gui.DestroyWindow(hwnd)

    return {
        "duration_sec": duration,
        "max_simultaneous_keys": max_keys,
        "nkro_supported": max_keys > 6,
        "heatmap": dict(heatmap),
    }

# ================= MAIN =================

if __name__ == "__main__":
    result = run_keyboard_test(10)

    print("\n=== TEST RESULT ===")
    print(f"Max simultaneous keys: {result['max_simultaneous_keys']}")
    print(f"NKRO supported: {result['nkro_supported']}")
    print(f"Unique keys pressed: {len(result['heatmap'])}")
