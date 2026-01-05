import re
import wmi


VID_PID_RE = re.compile(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", re.I)


def _resolve_usb_vid_pid_from_pnp(pnp_id: str, c: wmi.WMI):
    """
    Walk up the PnP tree to find VID/PID for USBSTOR devices.
    """
    try:
        devices = c.Win32_PnPEntity(PNPDeviceID=pnp_id)
        if not devices:
            return None, None

        parent_id = devices[0].Parent

        while parent_id:
            parents = c.Win32_PnPEntity(PNPDeviceID=parent_id)
            if not parents:
                break

            parent = parents[0]
            m = VID_PID_RE.search(parent.PNPDeviceID)
            if m:
                return m.group(1), m.group(2)

            parent_id = parent.Parent

    except Exception:
        pass

    return None, None


def get_storage_device_from_path(path: str) -> dict | None:
    """
    Resolve drive letter (C:\\) to physical storage device info.
    """
    drive_letter = path.rstrip("\\")
    c = wmi.WMI()

    for disk in c.Win32_LogicalDisk(DeviceID=drive_letter):
        for part in disk.associators("Win32_LogicalDiskToPartition"):
            for drive in part.associators("Win32_DiskDriveToDiskPartition"):

                info = {
                    "model": drive.Model,
                    "interface": drive.InterfaceType,
                    "bus": drive.InterfaceType,
                    "serial": drive.SerialNumber.strip() if drive.SerialNumber else None,
                    "pnp_id": drive.PNPDeviceID,
                    "vid": None,
                    "pid": None,
                }

                # ===== USB FIX =====
                if drive.PNPDeviceID and drive.PNPDeviceID.startswith("USBSTOR\\"):
                    vid, pid = _resolve_usb_vid_pid_from_pnp(drive.PNPDeviceID, c)
                    info["vid"] = vid
                    info["pid"] = pid

                return info

    return None
