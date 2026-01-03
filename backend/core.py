"""Core backend service for ProjectUSB."""
import datetime
from pathlib import Path

import backend.modules.testingModule as testingModule
import backend.modules.usbMonitoring as usbMonitoring
import backend.modules.hwTests.keyboard.keyboardWindows as keyboardTest
from backend.modules.hwTests.keyboard.keyboard_service import KeyboardTestWorker
from backend.modules.scanCodeConvert import scancode_to_key


class BackendService:
    """Main backend service class that handles business logic."""

    def __init__(self):
        """Initialize the backend service."""
        self._data = {}

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

    def resolve_scancode(self, scancode: int) -> str:
        return scancode_to_key(scancode)

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