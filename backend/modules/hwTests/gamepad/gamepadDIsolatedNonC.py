import pygame
import time
import math
from collections import defaultdict
import numpy as np

# ================= GAMEPAD DIRECTINPUT TEST MODULE =================
# This module uses pygame (which wraps DirectInput on Windows) to test gamepads.
# It supports:
# - Button heatmap (press counts, including analog triggers if reported as buttons)
# - Analog stick testing: min/max, center drift, deadzone estimation
# - Circularity error (average % deviation from perfect circle when moving stick to edge)
# - Polling rate estimation (by detecting state changes)
#
# Requirements: pip install pygame numpy
# Run on Windows 10+ with gamepad connected (works great with DualShock 4 in DirectInput mode)

pygame.init()
pygame.joystick.init()

def find_gamepad(vid=None, pid=None):
    """Find a connected joystick/gamepad, optionally by VID/PID (hex)."""
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        name = joy.get_name()
        guid = joy.get_guid()
        # GUID format example for DS4: 050000004c050000cc09000000000000 -> VID 054C, PID 09CC
        if len(guid) >= 12:
            try:
                extracted_vid = int(guid[8:12], 16)
                extracted_pid = int(guid[4:8], 16)
            except ValueError:
                extracted_vid = extracted_pid = None
        else:
            extracted_vid = extracted_pid = None

        if (vid is None and pid is None) or (extracted_vid == vid and extracted_pid == pid):
            print(f"Found gamepad: {name} (VID:0x{extracted_vid:04X} PID:0x{extracted_pid:04X})")
            return joy

    raise RuntimeError("No matching gamepad found. Connect your controller and try again.")

def run_gamepad_test(vid=None, pid=None, duration=20):
    """
    Run a comprehensive gamepad test.
    - Move sticks fully around in circles multiple times
    - Press all buttons (including triggers if analog)
    - Leave sticks at rest for drift measurement
    """
    joy = find_gamepad(vid, pid)

    num_axes = joy.get_numaxes()
    num_buttons = joy.get_numbuttons()
    num_hats = joy.get_numhats()

    print(f"\nDetected: {num_axes} axes, {num_buttons} buttons, {num_hats} hats")
    print("Testing... Move both sticks in wide circles, press all buttons/triggers, then leave at rest.")

    button_counts = defaultdict(int)
    axis_samples = defaultdict(list)       # all samples per axis
    stick_samples = {"left": [], "right": []}  # only outer samples for circularity
    change_times = []
    last_state = None
    start_time = time.time()

    while time.time() - start_time < duration:
        pygame.event.pump()  # process events

        # Buttons
        for b in range(num_buttons):
            if joy.get_button(b):
                button_counts[b] += 1

        # Axes (normalized -1 to 1)
        axes = [joy.get_axis(a) for a in range(num_axes)]

        # Hats (POV) as (dx, dy)
        hats = [joy.get_hat(h) for h in range(num_hats)]

        current_state = tuple(axes + [item for hat in hats for item in hat] +
                              [joy.get_button(b) for b in range(num_buttons)])

        if last_state is not None and current_state != last_state:
            change_times.append(time.time())

        last_state = current_state

        # Record all axis samples
        for a in range(num_axes):
            axis_samples[a].append(axes[a])

        # Assume common layout:
        # Left stick: axis 0 (X), 1 (Y)   Right stick: 2 (X), 3 (Y)
        # Triggers (if separate axes): L2 axis 4 or 5, R2 axis 5 (depends on driver)
        if num_axes >= 4:
            lx, ly = axes[0], axes[1]
            rx, ry = axes[2], axes[3]
            axis_samples["left_x"].append(lx)
            axis_samples["left_y"].append(ly)
            axis_samples["right_x"].append(rx)
            axis_samples["right_y"].append(ry)

            # Collect outer samples for circularity (radius > 0.9)
            l_radius = math.hypot(lx, ly)
            r_radius = math.hypot(rx, ry)
            if l_radius > 0.9:
                stick_samples["left"].append((lx, ly))
            if r_radius > 0.9:
                stick_samples["right"].append((rx, ry))

        time.sleep(0.001)  # ~1000 Hz polling

    # ================= ANALYSIS =================

    # Polling rate from state changes
    polling_rate = 0
    if len(change_times) > 1:
        intervals = np.diff(change_times)
        polling_rate = round(1 / intervals.mean())

    # Button heatmap
    buttons = {f"button_{k}": v for k, v in button_counts.items() if v > 0}

    # Axes / Sticks stats
    axes_stats = {}
    for name, samples in [("left_x", axis_samples.get("left_x", [])),
                          ("left_y", axis_samples.get("left_y", [])),
                          ("right_x", axis_samples.get("right_x", [])),
                          ("right_y", axis_samples.get("right_y", []))]:
        if samples:
            arr = np.array(samples)
            axes_stats[name] = {
                "min": round(float(arr.min()), 4),
                "max": round(float(arr.max()), 4),
                "center_avg": round(float(arr.mean()), 4),
                "drift_magnitude": round(float(np.mean(np.abs(arr))), 4),  # average deviation from 0 at rest
                "std": round(float(arr.std()), 4),
            }

    # Estimated inner deadzone (typical threshold where axis starts moving)
    def estimate_deadzone(samples):
        if not samples:
            return 0.0
        arr = np.abs(np.array(samples))
        return round(float(np.percentile(arr[arr > 0], 5)), 4) if len(arr[arr > 0]) > 0 else 0.0

    if "left_x" in axes_stats:
        axes_stats["left_deadzone_est"] = estimate_deadzone(axis_samples.get("left_x", []) + axis_samples.get("left_y", []))

    if "right_x" in axes_stats:
        axes_stats["right_deadzone_est"] = estimate_deadzone(axis_samples.get("right_x", []) + axis_samples.get("right_y", []))

    # Circularity error for outer movement
    def circularity_error(points):
        if len(points) < 20:  # need enough samples
            return None
        x, y = zip(*points)
        x = np.array(x)
        y = np.array(y)
        radii = np.hypot(x, y)
        avg_radius = radii.mean()
        deviations = np.abs(radii - avg_radius) / avg_radius * 100
        return round(float(deviations.mean()), 2)

    circularity = {
        "left": circularity_error(stick_samples["left"]),
        "right": circularity_error(stick_samples["right"]),
    }

    return {
        "polling_rate_hz": polling_rate,
        "buttons_pressed": buttons,
        "axes_stats": axes_stats,
        "circularity_error_percent": circularity,
        "raw_axis_count": num_axes,
        "raw_button_count": num_buttons,
    }

# ================= MAIN =================
if __name__ == "__main__":
    # Example: DualShock 4 - set to None to auto-detect first gamepad
    VID = 0x054C
    PID = 0x09CC

    try:
        result = run_gamepad_test(VID, PID, duration=20)

        print("\n=== DIRECTINPUT GAMEPAD TEST RESULT ===")
        print(f"Estimated polling rate: {result['polling_rate_hz']} Hz\n")

        print("Pressed buttons (count):")
        for b, c in sorted(result['buttons_pressed'].items(), key=lambda x: int(x[0].split("_")[1])):
            print(f"  {b:12}: {c}")

        print("\nAnalog sticks:")
        for key in ["left_x", "left_y", "right_x", "right_y"]:
            if key in result['axes_stats']:
                stats = result['axes_stats'][key]
                print(f"  {key:9}: min={stats['min']} max={stats['max']} center_avg={stats['center_avg']} "
                      f"drift={stats['drift_magnitude']} std={stats['std']}")

        if "left_deadzone_est" in result['axes_stats']:
            print(f"  Left stick estimated inner deadzone: ~{result['axes_stats']['left_deadzone_est']}")
        if "right_deadzone_est" in result['axes_stats']:
            print(f"  Right stick estimated inner deadzone: ~{result['axes_stats']['right_deadzone_est']}")

        print("\nCircularity error (lower = better circle when moving stick to edge):")
        print(f"  Left stick:  {result['circularity_error_percent']['left']}%")
        print(f"  Right stick: {result['circularity_error_percent']['right']}%")
        print("  (Typical good values: 5-12%; 0% may indicate aggressive clamping)")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your gamepad is connected and pygame is installed: pip install pygame numpy")