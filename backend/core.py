"""Core backend service for ProjectUSB."""

import backend.modules.testingModule as testingModule


class BackendService:
    """Main backend service class that handles business logic."""

    def __init__(self):
        """Initialize the backend service."""
        self._data = {}
        print(testingModule.test())

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
