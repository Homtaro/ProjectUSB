import ctypes
import time
import math
from collections import defaultdict

# ================= CONSTANTS =================

XINPUT_DLLS = ["xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"]
ERROR_SUCCESS = 0


# Button flags
BUTTON_MAP = {
    0x0001: "dpad_up",
    0x0002: "dpad_down",
    0x0004: "dpad_left",
    0x0008: "dpad_right",
    0x0010: "start",
    0x0020: "back",
    0x0040: "left_stick",
    0x0080: "right_stick",
    0x0100: "left_shoulder",
    0x0200: "right_shoulder",
    0x1000: "a",
    0x2000: "b",
    0x4000: "x",
    0x8000: "y",
}

# ================= GLOBAL STATE =================

button_heatmap = defaultdict(int)
left_stick_radii = []
right_stick_radii = []

trigger_lt = []
trigger_rt = []

packet_times = []

last_buttons = 0



# ================= XINPUT STRUCTS =================

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


# ================= XINPUT LOAD =================

_xinput = None
for dll in XINPUT_DLLS:
    try:
        _xinput = ctypes.windll.LoadLibrary(dll)
        break
    except OSError:
        pass

if not _xinput:
    raise RuntimeError("XInput not available")

_xinput.XInputGetState.argtypes = [ctypes.c_uint, ctypes.POINTER(XINPUT_STATE)]
_xinput.XInputGetState.restype = ctypes.c_uint

# ================= HELPERS =================

def normalize_axis(v):
    return v / 32767.0


def magnitude(x, y):
    return math.sqrt(x * x + y * y)


# ================= TEST RUNNER =================

def run_gamepad_test(controller_index=0, duration=10):
    """
    NOTE:
    XInput does NOT expose VID/PID.
    Device selection is done via controller slot (0–3).
    """

    global last_buttons
    button_heatmap.clear()
    left_stick_radii.clear()
    right_stick_radii.clear()
    trigger_lt.clear()
    trigger_rt.clear()
    packet_times.clear()

    state = XINPUT_STATE()
    last_packet = None

    print(f">>> Testing XInput controller #{controller_index} for {duration}s")

    start = time.time()

    while time.time() - start < duration:
        res = _xinput.XInputGetState(controller_index, ctypes.byref(state))
        if res != ERROR_SUCCESS:
            time.sleep(0.01)
            continue

        if state.dwPacketNumber == last_packet:
            continue
        last_packet = state.dwPacketNumber

        now = time.time()
        packet_times.append(now)

        gp = state.Gamepad

        # ================= BUTTONS =================
        # for mask, name in BUTTON_MAP.items():
        #     if gp.wButtons & mask:
        #         button_heatmap[name] += 1

        pressed_now = gp.wButtons
        pressed_prev = last_buttons

        for mask, name in BUTTON_MAP.items():
            # rising edge: was not pressed, now pressed
            if (pressed_now & mask) and not (pressed_prev & mask):
                button_heatmap[name] += 1

        last_buttons = pressed_now

        # ================= TRIGGERS =================
        trigger_lt.append(gp.bLeftTrigger)
        trigger_rt.append(gp.bRightTrigger)

        # ================= STICKS =================
        lx = normalize_axis(gp.sThumbLX)
        ly = normalize_axis(gp.sThumbLY)
        rx = normalize_axis(gp.sThumbRX)
        ry = normalize_axis(gp.sThumbRY)

        left_stick_radii.append(magnitude(lx, ly))
        right_stick_radii.append(magnitude(rx, ry))

        time.sleep(0.001)

    # ================= ANALYSIS =================

    polling_rate = 0
    if len(packet_times) > 1:
        intervals = [
            packet_times[i] - packet_times[i - 1]
            for i in range(1, len(packet_times))
        ]
        avg_interval = sum(intervals) / len(intervals)
        polling_rate = round(1 / avg_interval)

    def analyze_stick(radii):
        if not radii:
            return {}

        avg = sum(radii) / len(radii)
        return {
            "max_radius": round(max(radii), 3),
            "avg_radius": round(avg, 3),
            "circular_error": round(
                sum(abs(r - avg) for r in radii) / len(radii), 4
            ),
        }

    return {
        "duration_sec": duration,
        "polling_rate_hz": polling_rate,
        "button_heatmap": dict(button_heatmap),
        "left_stick": analyze_stick(left_stick_radii),
        "right_stick": analyze_stick(right_stick_radii),
        "triggers": {
            "lt_min": min(trigger_lt) if trigger_lt else 0,
            "lt_max": max(trigger_lt) if trigger_lt else 0,
            "rt_min": min(trigger_rt) if trigger_rt else 0,
            "rt_max": max(trigger_rt) if trigger_rt else 0,
        },
    }

# ================= HELPERS =================

def detect_active_controllers():
    active = []
    state = XINPUT_STATE()

    for idx in range(4):
        res = _xinput.XInputGetState(idx, ctypes.byref(state))
        if res == ERROR_SUCCESS:
            active.append(idx)

    return active


def select_controller(timeout=10):
    print("Press A on the controller to select...")
    start = time.time()
    state = XINPUT_STATE()

    last_packets = [0, 0, 0, 0]

    while time.time() - start < timeout:
        for idx in range(4):
            res = _xinput.XInputGetState(idx, ctypes.byref(state))
            if res != ERROR_SUCCESS:
                continue

            if state.dwPacketNumber != last_packets[idx]:
                last_packets[idx] = state.dwPacketNumber
                if state.Gamepad.wButtons & 0x1000:  # A button
                    print(f"Selected controller index: {idx}")
                    return idx

        time.sleep(0.01)

    raise TimeoutError("No controller selected")






# ================= MAIN =================

if __name__ == "__main__":
    result = run_gamepad_test(controller_index=0, duration=4)

    print("\n=== GAMEPAD TEST RESULT ===")
    print(f"Polling rate: {result['polling_rate_hz']} Hz")

    print("\nButton heatmap:")
    for k, v in result["button_heatmap"].items():
        print(f"  {k}: {v}")

    print("\nLeft stick:")
    for k, v in result["left_stick"].items():
        print(f"  {k}: {v}")

    print("\nRight stick:")
    for k, v in result["right_stick"].items():
        print(f"  {k}: {v}")

    print("\nTriggers:")
    for k, v in result["triggers"].items():
        print(f"  {k}: {v}")
