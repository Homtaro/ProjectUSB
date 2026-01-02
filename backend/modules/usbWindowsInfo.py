import win32com.client

# def get_windows_usb_devices():
#     wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")
#     svc = wmi.ConnectServer(".", "root\\cimv2")
#
#     devices = []
#     for dev in svc.ExecQuery("SELECT * FROM Win32_PnPEntity WHERE PNPClass='USB'"):
#         devices.append({
#             "device_id": dev.DeviceID,
#             "name": dev.Name,
#             "manufacturer": dev.Manufacturer,
#             "driver": dev.Service,
#             "status": dev.Status
#         })
#     return devices

def get_windows_usb_devices():
    wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")
    svc = wmi.ConnectServer(".", "root\\cimv2")

    devices = []
    for dev in svc.ExecQuery(
        "SELECT * FROM Win32_PnPEntity WHERE DeviceID LIKE '%VID_%'"
    ):
        devices.append({
            "device_id": dev.DeviceID,
            "name": dev.Name,
            "manufacturer": dev.Manufacturer,
            "driver": dev.Service,
            "status": dev.Status,
            "pnp_class": dev.PNPClass
        })
    return devices




def provide_windows_info(info, windows_devices):
    vidpid = f"VID_{int(info['vid'],16):04X}&PID_{int(info['pid'],16):04X}"

    for win in windows_devices:
        if vidpid in win["device_id"]:
            info["windows"] = {
                "friendly_name": win["name"],
                "driver": win["driver"],
                "status": win["status"]
            }
            break


#Testing purposes
if __name__ == "__main__":
    #print with formatting
    usb_devices = get_windows_usb_devices()
    for dev in usb_devices:
        print(f"Device ID: {dev['device_id']}")
        for key, value in dev.items():
            print(f"  {key}: {value}")
        print()