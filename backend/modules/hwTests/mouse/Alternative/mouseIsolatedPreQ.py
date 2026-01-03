import win32gui
import win32con
import ctypes
import time
import math
from collections import defaultdict

# ================= CONSTANTS =================

WM_INPUT = 0x00FF
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
RIDI_DEVICENAME = 0x20000007

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong,
    ctypes.c_void_p,
    ctypes.c_uint,
    ctypes.c_uint64,
    ctypes.c_int64
)

# ================= GLOBAL STATE =================

TARGET_VID = None
TARGET_PID = None

button_heatmap = defaultdict(int)
movement_points = []        # (dx, dy)
movement_times = []         # timestamps
jitter_samples = []         # magnitude of movement
packet_times = []           # timestamps for polling rate

wheel_v_accum = 0
wheel_h_accum = 0

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
        _fields_ = [
            ("mouse", RAWMOUSE),
        ]
    _fields_ = [
        ("header", RAWINPUTHEADER),
        # In 64-bit, there is 8-byte alignment here. 
        # Using a nested Union/Structure handles this automatically.
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
    global wheel_v_accum, wheel_h_accum


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

        if raw.header.dwType != RIM_TYPEMOUSE:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        if not device_matches_target(raw.header.hDevice):
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        now = time.time()
        packet_times.append(now)

        mouse = raw.data.mouse
        dx, dy = mouse.lLastX, mouse.lLastY

        # ================= MOVEMENT =================
        if dx != 0 or dy != 0:
            movement_points.append((dx, dy))
            movement_times.append(now)
            jitter_samples.append(math.hypot(dx, dy))

        # ================= BUTTONS =================
        #flags = mouse.usButtonFlags
        flags = mouse.u.s.usButtonFlags

        #print(f"Button flags: {flags}")

        # BUTTON_MAP = {
        #     0x0001: "left",
        #     0x0002: "left",
        #     0x0004: "right",
        #     0x0008: "right",
        #     0x0010: "middle",
        #     0x0020: "middle",
        #     0x0040: "x1",
        #     0x0080: "x1",
        #     0x0100: "x2",
        #     0x0200: "x2",
        # }

        BUTTON_MAP = {
            0x0001: "left",  # RI_MOUSE_LEFT_BUTTON_DOWN
            0x0004: "right",  # RI_MOUSE_RIGHT_BUTTON_DOWN
            0x0010: "middle",  # RI_MOUSE_MIDDLE_BUTTON_DOWN
            0x0040: "x1",  # RI_MOUSE_BUTTON_4_DOWN
            0x0100: "x2",  # RI_MOUSE_BUTTON_5_DOWN
        }

        for flag, name in BUTTON_MAP.items():
            if flags & flag:
                button_heatmap[name] += 1

            # if flags & 0x0400:  # RI_MOUSE_WHEEL
            #     delta = ctypes.c_short(mouse.u.s.usButtonData).value
            #     if delta > 0:
            #         button_heatmap["wheel_up"] += 1
            #     elif delta < 0:
            #         button_heatmap["wheel_down"] += 1
            #
            # if flags & 0x0800:  # RI_MOUSE_HWHEEL
            #     delta = ctypes.c_short(mouse.u.s.usButtonData).value
            #     if delta > 0:
            #         button_heatmap["wheel_right"] += 1
            #     elif delta < 0:
            #         button_heatmap["wheel_left"] += 1

        # ================= WHEEL =================
        if flags & 0x0400:  # RI_MOUSE_WHEEL
            delta = ctypes.c_short(mouse.u.s.usButtonData).value
            wheel_v_accum += delta

            while abs(wheel_v_accum) >= 120:
                if wheel_v_accum > 0:
                    button_heatmap["wheel_up"] += 1
                    wheel_v_accum -= 120
                else:
                    button_heatmap["wheel_down"] += 1
                    wheel_v_accum += 120

        if flags & 0x0800:  # RI_MOUSE_HWHEEL
            delta = ctypes.c_short(mouse.u.s.usButtonData).value
            wheel_h_accum += delta

            while abs(wheel_h_accum) >= 120:
                if wheel_h_accum > 0:
                    button_heatmap["wheel_right"] += 1
                    wheel_h_accum -= 120
                else:
                    button_heatmap["wheel_left"] += 1
                    wheel_h_accum += 120

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

# ================= RAW INPUT REGISTRATION =================

def register_mouse(hwnd):
    rid = RAWINPUTDEVICE(
        usUsagePage=0x01,   # Generic Desktop
        usUsage=0x02,       # Mouse
        dwFlags=RIDEV_INPUTSINK,
        hwndTarget=hwnd
    )

    if not ctypes.windll.user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(rid)
    ):
        raise ctypes.WinError()

# ================= TEST RUNNER =================

def run_mouse_test(vid, pid, duration=10):
    global TARGET_VID, TARGET_PID
    global _proc_keepalive

    TARGET_VID = vid
    TARGET_PID = pid

    button_heatmap.clear()
    movement_points.clear()
    movement_times.clear()
    jitter_samples.clear()
    packet_times.clear()

    _proc_keepalive = WNDPROC(wnd_proc)

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _proc_keepalive
    wc.lpszClassName = "RawInputMouseTest"
    wc.hInstance = win32gui.GetModuleHandle(None)

    try:
        win32gui.RegisterClass(wc)
    except win32gui.error:
        pass

    hwnd = win32gui.CreateWindowEx(
        0,
        wc.lpszClassName,
        "HiddenRawInputMouseWindow",
        0,
        0, 0, 0, 0,
        0, 0,
        wc.hInstance,
        None
    )

    register_mouse(hwnd)

    print(f">>> Testing mouse VID={vid:04x} PID={pid:04x} for {duration}s")

    start = time.time()
    while time.time() - start < duration:
        win32gui.PumpWaitingMessages()
        #time.sleep(0.001)
        time.sleep(0)

    win32gui.DestroyWindow(hwnd)
    _proc_keepalive = None

    # ================= ANALYSIS =================

    polling_rate = 0
    if len(packet_times) > 1:
        intervals = [
            packet_times[i] - packet_times[i - 1]
            for i in range(1, len(packet_times))
        ]
        avg_interval = sum(intervals) / len(intervals)
        polling_rate = round(1 / avg_interval)

    avg_jitter = round(sum(jitter_samples) / len(jitter_samples), 4) if jitter_samples else 0

    return {
        "duration_sec": duration,
        "button_heatmap": dict(button_heatmap),
        "movement_samples": len(movement_points),
        "avg_jitter": avg_jitter,
        "polling_rate_hz": polling_rate,
        "raw_path": movement_points,
    }


# ================= MAIN =================

if __name__ == "__main__":
    VID = 0x046D  # example: Logitech
    PID = 0xC08B

    result = run_mouse_test(VID, PID, duration=5)

    print("\n=== MOUSE TEST RESULT ===")
    print(f"Polling rate: {result['polling_rate_hz']} Hz")
    print(f"Average jitter: {result['avg_jitter']}")
    print(f"Movement samples: {result['movement_samples']}")
    print(f"Heatmap raw: {result['button_heatmap']}")
    print("Button heatmap:")
    for btn, count in result["button_heatmap"].items():
        print(f"  {btn}: {count}")
