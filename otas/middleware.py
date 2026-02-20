from .client import OtasClient
from .exceptions import OtasConfigurationError
from .logger import logger

class OtasMiddleware:
    """
    Django middleware that captures all API traffic (request + response)
    and forwards it to the OTAS platform.

    Usage in settings.py:

        MIDDLEWARE = [
            ...
            "otas.OtasMiddleware",
        ]

    Add OTAS_SDK_KEY as an environment variable
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.client = self._initialize_client()

    def _initialize_client(self) -> OtasClient:
        """
        Read the SDK key from the OTAS_SDK_KEY environment variable and return
        an initialised OtasClient. Django settings are never used for the key
        to avoid accidental exposure in source-controlled config files.
        """
        import os

        sdk_key = os.environ.get("OTAS_SDK_KEY")
        if not sdk_key:
            raise OtasConfigurationError(
                "OTAS_SDK_KEY environment variable is not set. "
                "Export it before starting the server:\n"
                "  export OTAS_SDK_KEY='otas_...'"
            )

        client = OtasClient(sdk_key)
        client.authenticate()
        logger.info(
            "[OTAS] Initialised project: '%s' (id: %s) successfully!",
            client.project_name,
            client.project_id,
        )
        return client


    def __call__(self, request):
        # --- capture request ---
        request_data = self._capture_request(request)

        response = self.get_response(request)

        # --- capture response ---
        response_data = self._capture_response(response)

        # --- forward to OTAS ---
        self._send_to_otas(request_data, response_data)

        return response

    def _capture_request(self, request) -> dict:
        """Extract all relevant data from the incoming Django request."""
        # TODO: implement full capture logic
        return {}

    def _capture_response(self, response) -> dict:
        """Extract all relevant data from the outgoing Django response."""
        # TODO: implement full capture logic
        return {}

    def _send_to_otas(self, request_data: dict, response_data: dict) -> None:
        """Send the captured traffic data to the OTAS backend."""
        # TODO: implement forwarding logic
        pass