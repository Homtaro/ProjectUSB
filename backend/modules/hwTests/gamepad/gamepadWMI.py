import wmi
import re
import ctypes
from backend.modules.hwTests.gamepad.gamepadXIsolated import (
    XINPUT_STATE,
    _xinput,
    ERROR_SUCCESS
)
from backend.modules.usbDecoder import decode_device_alternative, decode_device


def get_xinput_to_usb_mapping():
    """
    Create deterministic mapping from XInput slots to real USB VID/PIDs
    by tracing IG_00 devices back to their parent USB devices via serial number.

    Returns:
        dict: Mapping of {xinput_slot: {vid, pid, name, serial}}
        None if mapping failed
    """
    c = wmi.WMI()

    # Step 1: Find all XInput IG_00 interface devices
    ig00_devices = []
    for device in c.Win32_PnPEntity():
        if device.DeviceID and 'IG_00' in device.DeviceID:
            parts = device.DeviceID.split('\\')
            if len(parts) >= 3:
                serial = parts[-1].split('&')[-1] if '&' in parts[-1] else parts[-1]

                # Filter: Only USB\VID_... devices, not HID\VID_...
                # The USB ones are the actual controllers
                if device.DeviceID.startswith('USB\\'):
                    ig00_devices.append({
                        'device_id': device.DeviceID,
                        'serial': serial,
                        'name': device.Name
                    })

    # Step 2: For each IG_00, find its parent USB device with real VID/PID
    usb_mappings = []
    for ig_dev in ig00_devices:
        for usb_dev in c.Win32_PnPEntity():
            if (usb_dev.DeviceID and
                    'USB' in usb_dev.DeviceID and
                    ig_dev['serial'] in usb_dev.DeviceID and
                    'IG_' not in usb_dev.DeviceID):

                vid_match = re.search(r'VID_([0-9A-F]{4})', usb_dev.DeviceID.upper())
                pid_match = re.search(r'PID_([0-9A-F]{4})', usb_dev.DeviceID.upper())

                if vid_match and pid_match:
                    usb_mappings.append({
                        'serial': ig_dev['serial'],
                        'vid': f'0x{vid_match.group(1)}',
                        'pid': f'0x{pid_match.group(1)}',
                        'name': usb_dev.Name,
                        'ig_device_id': ig_dev['device_id']
                    })
                    break

    # Step 3: Get active XInput slots
    state = XINPUT_STATE()
    active_slots = []
    for idx in range(4):
        if _xinput.XInputGetState(idx, ctypes.byref(state)) == ERROR_SUCCESS:
            active_slots.append(idx)

    if not active_slots or not usb_mappings:
        return None

    # Create mapping
    mapping = {}
    for slot, usb_info in zip(active_slots, usb_mappings):
        mapping[slot] = {
            'vid': int(usb_info['vid'], 16),
            'pid': int(usb_info['pid'], 16),
            'name': usb_info['name'],
            'decoded_name': decode_device_alternative(usb_info['vid'], usb_info['pid']),
            'serial': usb_info['serial']
        }

    return mapping


def get_controller_real_vidpid(xinput_slot):
    """
    Get the real VID/PID for a specific XInput slot.

    Args:
        xinput_slot: XInput controller slot (0-3)

    Returns:
        dict with 'vid', 'pid', 'name', 'serial' or None
    """
    mapping = get_xinput_to_usb_mapping()
    return mapping.get(xinput_slot) if mapping else None


if __name__ == "__main__":
    print("=== XInput Real Device Identifier ===\n")

    mapping = get_xinput_to_usb_mapping()

    if mapping:
        for slot, info in mapping.items():
            print(f"XInput Slot {slot}:")
            print(f"  Device: {info['name']}")
            print(f"  VID:PID: {info['vid']}:{info['pid']}")
            print(f"  Serial: {info['serial']}")
    else:
        print("No controllers detected or mapping failed")