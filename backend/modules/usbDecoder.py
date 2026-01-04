import json
from pathlib import Path

map_path = Path(__file__).resolve().parent.parent.parent / "tools" / "usb_database.json"

with open(map_path, "r") as f:
    usb_map = json.load(f)

# Expose maps
vendors_map = usb_map["vendors"]
devices_map = usb_map["devices"]
classes_map = usb_map["classes"]
subclasses_map = usb_map["subclasses"]
protocols_map = usb_map["protocols"]


def decode_vendor(vid):
    key = f"0x{vid:04x}"
    return vendors_map.get(key, "Unknown Vendor")


def decode_device(vid, pid):
    #print("vid:", vid, "pid:", pid)
    key = f"0x{vid:04x}:0x{pid:04x}"
    return devices_map.get(key, "Unknown Device")


def decode_device_alternative(vid, pid):

    if isinstance(vid, str):
        vid = int(vid, 16)

    if isinstance(pid, str):
        pid = int(pid, 16)

    key = f"0x{vid:04x}:0x{pid:04x}"

    return devices_map.get(key, "Unknown Device")


def decode_class(cls):
    key = f"0x{cls:02x}"
    return classes_map.get(key, "Unknown Class")


def decode_subclass(cls, sub):
    key = f"{cls:02x}:{sub:02x}"
    return subclasses_map.get(key, "Unknown Subclass")


def decode_protocol(cls, sub, proto):
    key = f"{cls:02x}:{sub:02x}:{proto:02x}"
    return protocols_map.get(key, "Unknown Protocol")

#Testing
if __name__ == "__main__":
    print(decode_vendor(0x046d))  # Logitech, Inc.
    print(decode_device(0x046d, 0xc534))  # Logitech USB Receiver
    print(decode_class(0x03))  # Human Interface Device
    print(decode_subclass(0x03, 0x01))  # Boot Interface Subclass
    print(decode_protocol(0x03, 0x01, 0x01))  # Keyboard
