"""Core backend service for ProjectUSB."""

import backend.modules.testingModule as testingModule
import backend.modules.usbMonitoring as usbMonitoring


class BackendService:
    """Main backend service class that handles business logic."""

    def __init__(self):
        """Initialize the backend service."""
        self._data = {}
        print(testingModule.test())
        print("Hello world")
        #usbMonitoring.test_check_usb()
        #usbMonitoring.check_usb_all()

        device_info_list = usbMonitoring.get_all_devices_info()
        for dev_info in device_info_list:
           print(dev_info)

        usbMonitoring.testing_decoder()

        device_info_list_decoded = usbMonitoring.get_all_devices_info_decoded()
        for dev_info in device_info_list_decoded:
            print(dev_info)

        devices = usbMonitoring.load_devices()

        for dev in devices:
            print(usbMonitoring.format_device_tree(dev))
            print("\n" + "=" * 50 + "\n")

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

#Remove Later
if __name__ == "__main__":
    backend = BackendService()