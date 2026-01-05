import re
import wmi

VID_PID_RE = re.compile(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", re.I)


def get_audio_device_info(device_name: str) -> dict | None:
    """
    Resolve WASAPI audio input device name to VID/PID + model.
    """
    c = wmi.WMI()

    for dev in c.Win32_PnPEntity():
        if not dev.Name or device_name not in dev.Name:
            continue

        info = {
            "name": dev.Name,
            "pnp_id": dev.PNPDeviceID,
            "vid": None,
            "pid": None,
            "bus": "USB" if dev.PNPDeviceID and "USB" in dev.PNPDeviceID else "UNKNOWN",
        }

        if dev.PNPDeviceID:
            m = VID_PID_RE.search(dev.PNPDeviceID)
            if m:
                info["vid"] = int(m.group(1), 16)
                info["pid"] = int(m.group(2), 16)

        return info

    return None
