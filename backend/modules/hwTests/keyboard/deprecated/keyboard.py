
import hid

def open_keyboard(vid, pid):
    keyboards = []

    for d in hid.enumerate(vid, pid):
        if d["usage_page"] == 0x01 and d["usage"] == 0x06:
            keyboards.append(d)

    # Prefer interface 0
    keyboards.sort(key=lambda d: d.get("interface_number", 99))

    if not keyboards:
        return None

    dev = hid.device()
    dev.open_path(keyboards[0]["path"])
    return dev


import time

def capture_keyboard(dev, seconds=10):
    reports = []
    end = time.perf_counter() + seconds

    while time.perf_counter() < end:
        try:
            data = dev.read(64, timeout_ms=50)
            if data:
                reports.append((
                    time.perf_counter_ns(),
                    bytes(data)
                ))
        except OSError:
            # Windows HID may throw transient read errors
            continue

    return reports


def parse_keys(report):
    # Boot keyboard
    if len(report) == 8:
        return {k for k in report[2:8] if k != 0}

    # NKRO bitmap (common pattern)
    pressed = set()
    for byte_index, byte in enumerate(report):
        for bit in range(8):
            if byte & (1 << bit):
                pressed.add(byte_index * 8 + bit)
    return pressed



def nkro_test(reports):
    max_keys = 0

    for _, report in reports:
        keys = parse_keys(report)
        max_keys = max(max_keys, len(keys))

    return {
        "max_simultaneous_keys": max_keys,
        "nkro_supported": max_keys > 6
    }


from collections import defaultdict

def heatmap_test(reports):
    heatmap = defaultdict(int)

    for _, report in reports:
        keys = parse_keys(report)
        for k in keys:
            heatmap[k] += 1

    return dict(heatmap)

def keyboard_test(dev, duration=10):
    reports = capture_keyboard(dev, duration)

    return {
        "nkro": nkro_test(reports),
        "heatmap": heatmap_test(reports),
        "sample_count": len(reports),
        "duration_sec": duration
    }


#Test
if __name__ == "__main__":
    dev = open_keyboard(0x258a, 0x10c)
    print(hid.enumerate(0x258a, 0x10c))
    data = dev.read(64, timeout_ms=50)
    if data:
        print(data)

    #print(keyboard_test(dev))
