import os
import json
import sys
import usb.core
import usb.util
from usb.backend.libusb1 import get_backend
from backend.modules.usbDecoder import (
    decode_vendor, decode_device, decode_class, decode_subclass, decode_protocol
)
from backend.modules.usbWindowsInfo import get_windows_usb_devices, provide_windows_info


# # Pathing
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))       # backend/modules
# BACKEND_DIR = os.path.dirname(CURRENT_DIR)                    # backend
#
# #DLLs
# x64_libusb_dll_path = os.path.join(BACKEND_DIR, "dlls", "libusb-1.0.dll")
#
# print("CURRENT:", CURRENT_DIR)
# print("BACKEND:", BACKEND_DIR)
# print("DLL PATH:", x64_libusb_dll_path)
#
# backend = get_backend(find_library=lambda name: x64_libusb_dll_path)
#
# if backend is None:
#     print("LibUSB backend not found. Ensure that libusb-1.0.dll is available.")
#     sys.exit(1)

#check backend
# print(backend)

def load_backend():
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    BACKEND_DIR = os.path.dirname(CURRENT_DIR)
    dll_path = os.path.join(BACKEND_DIR, "dlls", "libusb-1.0.dll")

    print("DLL PATH:", dll_path)

    backend = get_backend(find_library=lambda name: dll_path)

    if backend is None:
        print("LibUSB backend not found:", dll_path)
        return None

    return backend

def load_devices():

    backend = load_backend()
    if backend is None:
        print("Backend could not be loaded.")
        return

    devices = usb.core.find(find_all=True, backend=backend)
    return devices

def get_all_devices_info():
    devices = list(load_devices())
    return [get_device_info(dev) for dev in devices]

#def get_all_devices_info_decoded():
#    devices = list(load_devices())
#    return [get_device_info_decoded(dev) for dev in devices]

def get_all_devices_info_decoded():
    devices = list(load_devices())
    windows_devices = get_windows_usb_devices()

    result = []
    for dev in devices:
        info = get_device_info_decoded(dev)
        provide_windows_info(info, windows_devices)
        result.append(info)

    return result


def get_all_devices_full_info():
    devices = list(load_devices())
    windows_devices = get_windows_usb_devices()

    return [
        get_device_info_full(dev, windows_devices)
        for dev in devices
    ]


def is_keyboard_interface(interface):
    return (
        interface["class"] == "0x03" and
        interface["subclass"] == "0x01" and
        interface["protocol"] == "0x01"
    )

def test_check_usb():

    backend = load_backend()
    if backend is None:
        print("Backend could not be loaded.")
        return

    devices = usb.core.find(find_all=True, backend=backend)

    for dev in devices:
        print(f"VID:PID = {hex(dev.idVendor)}:{hex(dev.idProduct)}")
        print(f"USB Version: {hex(dev.bcdUSB)}")
        print(f"Device Class: {hex(dev.bDeviceClass)}")

        try:
            print("Manufacturer:", usb.util.get_string(dev, dev.iManufacturer))
            print("Product:", usb.util.get_string(dev, dev.iProduct))
            print("Serial Number:", usb.util.get_string(dev, dev.iSerialNumber))
        except:
            print("String read failed")

        cfg = dev[0]
        print(f"Max Power (mA): {cfg.bMaxPower * 2}")
        print(f"Self-Powered: {bool(cfg.bmAttributes & 0x40)}")

        print("------------------------------")

        #for d in usb.core.find(find_all=True, backend=backend):
        #    print("Device found:", hex(d.idVendor), hex(d.idProduct))

    return "USB Check Complete"

def check_usb_all():
    backend = load_backend()
    if backend is None:
        print("Backend could not be loaded.")
        return

    devices = usb.core.find(find_all=True, backend=backend)

    for dev in devices:
        print("====================================")
        print(f"VID:PID       = {hex(dev.idVendor)}:{hex(dev.idProduct)}")
        print(f"USB Version   = {hex(dev.bcdUSB)}")
        print(f"Device Class  = {hex(dev.bDeviceClass)}")

        # Strings
        try:
            manufacturer = usb.util.get_string(dev, dev.iManufacturer)
            product = usb.util.get_string(dev, dev.iProduct)
            serial = usb.util.get_string(dev, dev.iSerialNumber)
        except:
            manufacturer = product = serial = None

        print(f"Manufacturer  = {manufacturer}")
        print(f"Product       = {product}")
        print(f"Serial Number = {serial}")

        # Power info (from first configuration)
        #cfg = dev[0]

        try:
            cfg = dev.get_active_configuration()
        except usb.core.USBError:
            cfg = dev[0]  # fallback

        print(f"Max Power     = {cfg.bMaxPower * 2} mA")
        print(f"Self-Powered  = {bool(cfg.bmAttributes & 0x40)}")

        # ----- NEW: READ INTERFACE DESCRIPTORS -----
        print("Interfaces:")
        for interface in cfg:
            print(f"  Interface #{interface.bInterfaceNumber}")
            print(f"    Class      = {hex(interface.bInterfaceClass)}")
            print(f"    SubClass   = {hex(interface.bInterfaceSubClass)}")
            print(f"    Protocol   = {hex(interface.bInterfaceProtocol)}")

        print("====================================\n")

    return "USB Check Complete"

#DEPRECATED START
def classify_device(dev):
    for cfg in dev:
        for intf in cfg:
            cls = intf.bInterfaceClass

            if cls == 0x03:
                if intf.bInterfaceProtocol == 1:
                    return "Keyboard"
                if intf.bInterfaceProtocol == 2:
                    return "Mouse"
                return "Generic HID"

            if cls == 0x01:
                return "Audio (Microphone/Speaker)"

            if cls == 0x0E:
                return "Webcam"

            if cls == 0x09:
                return "USB Hub"

            if cls == 0xE0:
                return "Wireless Adapter / Bluetooth Radio"

    return "Unknown"
#DEPRECATED END


def get_device_info(dev):
    info = {
        "vid": hex(dev.idVendor),
        "pid": hex(dev.idProduct),
        "class": hex(dev.bDeviceClass),
        "manufacturer": None,
        "product": None,
        "serial": None,
        "power_mA": None,
        "self_powered": None,
        "interfaces": [],
        "type": None
    }

    try:
        info["manufacturer"] = usb.util.get_string(dev, dev.iManufacturer)
        info["product"] = usb.util.get_string(dev, dev.iProduct)
        info["serial"] = usb.util.get_string(dev, dev.iSerialNumber)
    except:
        pass

    #cfg = dev[0]

    try:
        cfg = dev.get_active_configuration()
    except (usb.core.USBError, NotImplementedError):
        cfg = dev[0]  # descriptor-only fallback (no device open)

    info["power_mA"] = cfg.bMaxPower * 2
    info["self_powered"] = bool(cfg.bmAttributes & 0x40)

    for intf in cfg:
        intf_info = {
            "number": intf.bInterfaceNumber,
            "class": hex(intf.bInterfaceClass),
            "subclass": hex(intf.bInterfaceSubClass),
            "protocol": hex(intf.bInterfaceProtocol)
        }
        info["interfaces"].append(intf_info)

    info["type"] = decode_class(dev.bDeviceClass)

    return info

# def get_device_info_decoded(dev):
#     info = {
#         "vid": hex(dev.idVendor),
#         "pid": hex(dev.idProduct),
#         "vendor_name": decode_vendor(dev.idVendor),
#         "device_name": decode_device(dev.idVendor, dev.idProduct),
#         "class": hex(dev.bDeviceClass),
#         "class_name": decode_class(dev.bDeviceClass),
#         "interfaces": []
#     }
#
#     cfg = dev[0]
#     for intf in cfg:
#         info["interfaces"].append({
#             "number": intf.bInterfaceNumber,
#             "class": hex(intf.bInterfaceClass),
#             "class_name": decode_class(intf.bInterfaceClass),
#             "subclass": hex(intf.bInterfaceSubClass),
#             "subclass_name": decode_subclass(
#                 intf.bInterfaceClass, intf.bInterfaceSubClass
#             ),
#             "protocol": hex(intf.bInterfaceProtocol),
#             "protocol_name": decode_protocol(
#                 intf.bInterfaceClass, intf.bInterfaceSubClass, intf.bInterfaceProtocol
#             )
#         })
#
#     return info

def get_device_info_decoded(dev):
    info = {
        "vid": hex(dev.idVendor),
        "pid": hex(dev.idProduct),
        "vendor_name": decode_vendor(dev.idVendor),
        "device_name": decode_device(dev.idVendor, dev.idProduct),
        "class": hex(dev.bDeviceClass),
        "class_name": decode_class(dev.bDeviceClass),
        "interfaces": []
    }

    try:
        cfg = dev.get_active_configuration()
    except (usb.core.USBError, NotImplementedError):
        cfg = dev[0]  # descriptor-only fallback (no device open)

    seen_interfaces = set()

    info["power"] = {
        "max_power_ma": cfg.bMaxPower * 2,
        "self_powered": bool(cfg.bmAttributes & 0x40)
    }

    for intf in cfg:
        key = (intf.bInterfaceNumber, intf.bInterfaceClass,
               intf.bInterfaceSubClass, intf.bInterfaceProtocol)

        if key in seen_interfaces:
            continue
        seen_interfaces.add(key)

        info["interfaces"].append({
            "number": intf.bInterfaceNumber,
            "class": hex(intf.bInterfaceClass),
            "class_name": decode_class(intf.bInterfaceClass),
            "subclass": hex(intf.bInterfaceSubClass),
            "subclass_name": decode_subclass(
                intf.bInterfaceClass, intf.bInterfaceSubClass
            ),
            "protocol": hex(intf.bInterfaceProtocol),
            "protocol_name": decode_protocol(
                intf.bInterfaceClass,
                intf.bInterfaceSubClass,
                intf.bInterfaceProtocol
            )
        })

    return info


def get_device_info_full(dev, windows_devices=None):
    """
    Returns FULL normalized device info for frontend consumption.
    """

    info = {
        "vid": hex(dev.idVendor),
        "pid": hex(dev.idProduct),

        "vendor_name": decode_vendor(dev.idVendor),

        "device_name": decode_device(dev.idVendor, dev.idProduct),


        "usb_version": hex(dev.bcdUSB),
        
        "class": hex(dev.bDeviceClass),
        "class_name": decode_class(dev.bDeviceClass),

        "manufacturer": None,
        "product": None,
        "serial": None,

        "power": {},
        "interfaces": [],
    }

    # ---- Strings ----
    try:
        info["manufacturer"] = usb.util.get_string(dev, dev.iManufacturer)
        info["product"] = usb.util.get_string(dev, dev.iProduct)
        info["serial"] = usb.util.get_string(dev, dev.iSerialNumber)
    except Exception:
        pass

    # ---- Configuration ----
    try:
        cfg = dev.get_active_configuration()
    except (usb.core.USBError, NotImplementedError):
        cfg = dev[0]

    info["power"] = {
        "max_power_ma": cfg.bMaxPower * 2,
        "self_powered": bool(cfg.bmAttributes & 0x40),
    }

    seen = set()

    for intf in cfg:
        key = (
            intf.bInterfaceNumber,
            intf.bInterfaceClass,
            intf.bInterfaceSubClass,
            intf.bInterfaceProtocol,
        )

        if key in seen:
            continue
        seen.add(key)

        info["interfaces"].append({
            "number": intf.bInterfaceNumber,

            "class": hex(intf.bInterfaceClass),
            "class_name": decode_class(intf.bInterfaceClass),

            "subclass": hex(intf.bInterfaceSubClass),
            "subclass_name": decode_subclass(
                intf.bInterfaceClass, intf.bInterfaceSubClass
            ),

            "protocol": hex(intf.bInterfaceProtocol),
            "protocol_name": decode_protocol(
                intf.bInterfaceClass,
                intf.bInterfaceSubClass,
                intf.bInterfaceProtocol,
            ),
        })

    # ---- Windows enrichment ----
    if windows_devices:
        provide_windows_info(info, windows_devices)

    return info



def format_device_tree(dev):
    """Return a formatted tree-style USB information block."""
    info = get_device_info(dev)

    # Basic info
    basic = [
        f"VID:PID          -> '{info['vid']}:{info['pid']}'",
        f"Device Class     -> '{info['class']}'",
        f"USB Version      -> '{hex(dev.bcdUSB)}'",
        f"Manufacturer     -> '{info['manufacturer']}'",
        f"Product          -> '{info['product']}'",
        f"Serial Number    -> '{info['serial']}'"
    ]

    # Power info
    power = [
        f"Max Power (mA)   -> {info['power_mA']}",
        f"Self-Powered     -> {info['self_powered']}"
    ]

    # Interfaces
    interfaces = []
    for intf in info["interfaces"]:
        interfaces.append(
            f"│   ├─ Interface #{intf['number']}\n"
            f"│   │   ├─ Class        -> '{intf['class']}'\n"
            f"│   │   ├─ SubClass     -> '{intf['subclass']}'\n"
            f"│   │   └─ Protocol     -> '{intf['protocol']}'"
        )

    interfaces_block = "\n".join(interfaces) if interfaces else "│   └─ No Interfaces"

    # Device type
    device_type = f"'{info['type']}'"

    # Final formatted tree
    tree = (
        "USB Device\n"
        "├─ Basic Info\n" +
        "".join([f"│   ├─ {b}\n" for b in basic[:-1]]) +
        f"│   └─ {basic[-1]}\n"
        "│\n"
        "├─ Power Info\n" +
        f"│   ├─ {power[0]}\n"
        f"│   └─ {power[1]}\n"
        "│\n"
        "├─ Interfaces\n" +
        interfaces_block +
        "\n│\n"
        f"└─ Device Type           -> {device_type}"
    )

    return tree

# def format_device_tree_full(info: dict) -> str:
#     lines = []
#
#     lines.append("USB Device")
#     lines.append("├─ Basic Info")
#     lines.append(f"│   ├─ VID:PID          -> '{info['vid']}:{info['pid']}'")
#     lines.append(f"│   ├─ Device Class     -> '{info['class']}'")
#     lines.append(f"│   ├─ USB Version      -> '{info['usb_version']}'")
#     lines.append(f"│   ├─ Manufacturer     -> '{info['manufacturer']}'")
#     lines.append(f"│   ├─ Product          -> '{info['product']}'")
#     lines.append(f"│   └─ Serial Number    -> '{info['serial']}'")
#     lines.append("│")
#
#     lines.append("├─ Power Info")
#     lines.append(f"│   ├─ Max Power (mA)   -> {info['power']['max_power_ma']}")
#     lines.append(f"│   └─ Self-Powered     -> {info['power']['self_powered']}")
#     lines.append("│")
#
#     lines.append("├─ Interfaces")
#     for idx, intf in enumerate(info["interfaces"]):
#         prefix = "│   ├─" if idx < len(info["interfaces"]) - 1 else "│   └─"
#         lines.append(f"{prefix} Interface #{intf['number']}")
#         lines.append(f"│   │   ├─ Class        -> '{intf['class']}'")
#         lines.append(f"│   │   ├─ SubClass     -> '{intf['subclass']}'")
#         lines.append(f"│   │   └─ Protocol     -> '{intf['protocol']}'")
#
#     lines.append("│")
#     lines.append(f"└─ Device Type           -> '{info['class_name']}'")
#
#     if "windows" in info:
#         w = info["windows"]
#         lines.append("")
#         lines.append("Windows Info")
#         lines.append(f"├─ Friendly Name -> '{w.get('friendly_name')}'")
#         lines.append(f"├─ Driver        -> '{w.get('driver')}'")
#         lines.append(f"└─ Status        -> '{w.get('status')}'")
#
#     return "\n".join(lines)

def format_device_tree_full(info: dict) -> str:
    lines = []

    lines.append("USB Device")
    lines.append("├─ Basic Info")

    lines.append(
        f"│   ├─ VID:PID          -> "
        f"{info.get('vendor_name')} "
        f"[{info['vid']}:{info['pid']}]"
    )

    lines.append(
        f"│   ├─ Device Name      -> "
        f"{info.get('device_name')}"
    )

    lines.append(
        f"│   ├─ Device Class     -> "
        f"{info.get('class_name')} "
        f"[{info.get('class')}]"
    )

    lines.append(
        f"│   ├─ USB Version      -> {info.get('usb_version')}"
    )

    lines.append(
        f"│   ├─ Manufacturer     -> {info.get('manufacturer')}"
    )

    lines.append(
        f"│   ├─ Product          -> {info.get('product')}"
    )

    lines.append(
        f"│   └─ Serial Number    -> {info.get('serial')}"
    )

    lines.append("│")
    lines.append("├─ Power Info")
    lines.append(
        f"│   ├─ Max Power (mA)   -> {info['power'].get('max_power_ma')}"
    )
    lines.append(
        f"│   └─ Self-Powered     -> {info['power'].get('self_powered')}"
    )

    lines.append("│")
    lines.append("├─ Interfaces")

    for idx, intf in enumerate(info["interfaces"]):
        last = idx == len(info["interfaces"]) - 1
        prefix = "│   └─" if last else "│   ├─"

        lines.append(f"{prefix} Interface #{intf['number']}")

        lines.append(
            f"│   │   ├─ Class        -> "
            f"{intf['class_name']} [{intf['class']}]"
        )

        lines.append(
            f"│   │   ├─ SubClass     -> "
            f"{intf['subclass_name']} [{intf['subclass']}]"
        )

        lines.append(
            f"│   │   └─ Protocol     -> "
            f"{intf['protocol_name']} [{intf['protocol']}]"
        )

    lines.append("│")
    lines.append(
        f"└─ Device Type           -> {info.get('class_name')}"
    )

    if "windows" in info:
        w = info["windows"]
        lines.append("")
        lines.append("Windows Info")
        lines.append(f"├─ Friendly Name -> {w.get('friendly_name')}")
        lines.append(f"├─ Driver        -> {w.get('driver')}")
        lines.append(f"└─ Status        -> {w.get('status')}")

    return "\n".join(lines)


def resolve_display_name(info: dict) -> str:
    # 1. Windows friendly name
    windows = info.get("windows")
    if windows:
        name = windows.get("friendly_name")
        if name:
            return name

    # 2. Decoded device name (VID:PID)
    dev_name = info.get("device_name")
    if dev_name and dev_name != "Unknown Device":
        return dev_name

    # 3. Manufacturer + product string
    manufacturer = info.get("manufacturer")
    product = info.get("product")
    if manufacturer or product:
        return " ".join(filter(None, [manufacturer, product]))

    # 4. Interface-based classification
    classes = {i["class_name"] for i in info.get("interfaces", [])}
    if "Human Interface Device" in classes:
        if any(i["protocol_name"] == "Keyboard" for i in info["interfaces"]):
            return "Keyboard"
        if any(i["protocol_name"] == "Mouse" for i in info["interfaces"]):
            return "Mouse"
        return "HID Device"

    if "Audio" in classes:
        return "Audio Device"

    if "Video" in classes:
        return "Video Device"

    # 5. Fallback
    return "Unknown Device"

def testing_decoder():
    print(decode_vendor(0x046d))  # Logitech, Inc.
    print(decode_device(0x046d, 0xc534))  # Logitech USB Receiver
    print(decode_class(0x03))  # Human Interface Device
    print(decode_subclass(0x03, 0x01))  # Boot Interface Subclass
    print(decode_protocol(0x03, 0x01, 0x01))  # Keyboard
