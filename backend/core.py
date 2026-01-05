"""Core backend service for ProjectUSB."""
import datetime
from pathlib import Path

import backend.modules.testingModule as testingModule
import backend.modules.usbMonitoring as usbMonitoring
import backend.modules.hwTests.keyboard.keyboardWindows as keyboardTest
from backend.modules.hwTests.audio.audioIn_service import AudioInputTestWorker
from backend.modules.hwTests.audio.audioOut_service import AudioOutputTestWorker
from backend.modules.hwTests.gamepad.gamepadWMI import get_controller_real_vidpid
from backend.modules.hwTests.gamepad.gamepadXIsolated import detect_active_controllers
from backend.modules.hwTests.gamepad.gamepadX_Service import GamepadTestWorker
from backend.modules.hwTests.keyboard.keyboard_service import KeyboardTestWorker
from backend.modules.hwTests.mouse.mouse_service import MouseTestWorker
from backend.modules.hwTests.storage.storage_service import list_storage_paths, SingleFileStorageTestWorker, \
    MultiFileStorageTestWorker
from backend.modules.scanCodeConvert import scancode_to_key


class BackendService:
    """Main backend service class that handles business logic."""

    def __init__(self):
        """Initialize the backend service."""
        self._data = {}

        print(self.get_hid_keyboards())
        print(self.get_hid_mouse())

        # print(testingModule.test())
        # print("Hello world")
        #
        # usbMonitoring.testing_decoder()
        #
        # device_info_list = usbMonitoring.get_all_devices_info()
        # for dev_info in device_info_list:
        #    print(dev_info)
        #
        # device_info_list_decoded = usbMonitoring.get_all_devices_info_decoded()
        # for dev_info in device_info_list_decoded:
        #     print(dev_info)
        #
        # devices = usbMonitoring.load_devices()
        #
        # for dev in devices:
        #     print(usbMonitoring.format_device_tree(dev))
        #     print("\n" + "=" * 50 + "\n")



    def get_status(self) -> str:
        """Get the current status of the backend service.

        Returns:
            str: Status message indicating the service state.
        """
        return "Backend service is running"

    def process_data(self, data: str) -> str:
        """Process input data and return a result.

        Args:
            data: Input data to process.

        Returns:
            str: Processed result.
        """
        result = f"Processed: {data}"
        self._data["last_input"] = data
        self._data["last_result"] = result
        return result

    def get_last_result(self) -> str | None:
        """Get the last processed result.

        Returns:
            str | None: The last processed result or None if no data has been processed.
        """
        return self._data.get("last_result")

    def get_usb_devices(self):
        """
        Returns decoded USB device info list
        """
        return usbMonitoring.get_all_devices_info_decoded()

    def get_usb_devices_full(self):
        """
        Returns full USB device info list
        """
        return usbMonitoring.get_all_devices_full_info()

    def resolve_device_name_format(self, info: dict) -> str:
        """
        Resolve best display name for device info dict
        """
        return usbMonitoring.resolve_display_name(info)

    def create_keyboard_test(self, vid: int, pid: int, duration: int = 0) -> KeyboardTestWorker:
        """
        Create a keyboard test worker for given device.
        UI owns the thread lifecycle.
        """
        return KeyboardTestWorker(
            vid=vid,
            pid=pid,
            duration=duration
        )

    def create_mouse_test(self, vid: int, pid: int, duration: int = 10) -> MouseTestWorker:
        """
        Create a mouse test worker for given device.
        UI owns the thread lifecycle.
        """
        return MouseTestWorker(
            vid=vid,
            pid=pid,
            duration=duration
        )

    # def create_gamepad_test(self, controller_index: int | None = None) -> GamepadTestWorker:
    #     """
    #     Create XInput gamepad test worker.
    #     UI owns the thread lifecycle.
    #     """
    #     return GamepadTestWorker(
    #         controller_index=controller_index
    #     )

    def create_gamepad_test(self, controller_index: int | None = None) -> GamepadTestWorker:
        # Resolve controller index FIRST (main thread)
        if controller_index is None:
            active = detect_active_controllers()
            if not active:
                raise RuntimeError("No XInput controllers detected")
            controller_index = active[0]

        #WMI CALL
        device_info = get_controller_real_vidpid(controller_index) or {}

        return GamepadTestWorker(
            controller_index=controller_index,
            device_info=device_info,  # injected
        )

    def list_audio_input_devices(self):
        return AudioInputTestWorker.list_devices()

    def list_audio_output_devices(self):
        return AudioOutputTestWorker.list_devices()

    def create_audio_input_test(self, device_index: int):
        return AudioInputTestWorker(device_index)

    def create_audio_output_test(self, device_index: int):
        return AudioOutputTestWorker(device_index)





    def get_hid_keyboards(self) -> list[dict]:
        """
        Returns list of HID keyboard devices (interface-level detection).
        """
        devices = usbMonitoring.get_all_devices_info_decoded()
        keyboards = []

        # for dev in usbMonitoring.get_all_devices_info_decoded():
        #     print(dev["device_name"])
        #     for i in dev["interfaces"]:
        #         print(" ", i["class_name"], i["subclass_name"], i["protocol_name"])

        for dev in devices:
            for intf in dev.get("interfaces", []):
                if (
                        intf.get("class_name") == "Human Interface Device"
                        and "Boot" in intf.get("subclass_name", "")
                        and intf.get("protocol_name") == "Keyboard"
                ):
                    keyboards.append({
                        "name": dev["device_name"],
                        "vid": int(dev["vid"], 16),
                        "pid": int(dev["pid"], 16),
                        "interface": intf["number"],
                    })
                    break  # one keyboard interface is enough

        return keyboards


    def get_hid_mouse(self) -> list[dict]:
        """
        Returns list of HID keyboard devices (interface-level detection).
        """
        devices = usbMonitoring.get_all_devices_info_decoded()
        mice = []

        for dev in devices:
            for intf in dev.get("interfaces", []):
                if (
                        intf.get("class_name") == "Human Interface Device"
                        and "Boot" in intf.get("subclass_name", "")
                        and intf.get("protocol_name") == "Mouse"
                ):
                    mice.append({
                        "name": dev["device_name"],
                        "vid": int(dev["vid"], 16),
                        "pid": int(dev["pid"], 16),
                        "interface": intf["number"],
                    })
                    break  # one keyboard interface is enough

        return mice

    def list_storage_devices(self):
        return list_storage_paths()

    def create_single_file_storage_test(self, path: str):
        return SingleFileStorageTestWorker(path)

    def create_multi_file_storage_test(self, path: str):
        return MultiFileStorageTestWorker(path)

    def resolve_scancode(self, scancode: int) -> str:
        return scancode_to_key(scancode)

    @staticmethod
    def get_journal_path_device(test_name: str, device: dict):
        from datetime import datetime
        from pathlib import Path

        root = Path.cwd() / "journal"
        root.mkdir(exist_ok=True)

        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # ---- device tag resolution ----
        if device.get("vid") and device.get("pid"):
            dev_tag = f"{device['vid']:04X}_{device['pid']:04X}"

        elif device.get("model"):
            dev_tag = device["model"]

        elif device.get("name"):
            dev_tag = device["name"]

        else:
            dev_tag = "UNKNOWN_DEVICE"

        dev_tag = dev_tag.replace(" ", "_")[:32]

        base = f"{test_name}[{dev_tag}]_{date}"

        i = 1
        while True:
            path = root / f"{base}_{i}.json"
            if not path.exists():
                return path
            i += 1

    @staticmethod
    def get_journal_path(test_name: str, vid: int, pid: int):
        from datetime import datetime
        from pathlib import Path

        root = Path.cwd() / "journal"
        root.mkdir(exist_ok=True)

        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base = f"{test_name}[{vid:04X}_{pid:04X}]_{date}"

        i = 1
        while True:
            path = root / f"{base}_{i}.json"
            if not path.exists():
                return path
            i += 1


#Remove Later
if __name__ == "__main__":
    backend = BackendService()