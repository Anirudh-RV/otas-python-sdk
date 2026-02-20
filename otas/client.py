from .auth import authenticate
from .exceptions import OtasConfigurationError


class OtasClient:
    """
    Central client that authenticates with the OTAS backend
    and holds project credentials for use by the middleware.
    """

    def __init__(self, sdk_key: str):
        if not sdk_key:
            raise OtasConfigurationError("sdk_key must not be empty.")

        self.sdk_key = sdk_key
        self._credentials: dict | None = None

    def authenticate(self) -> "OtasClient":
        """
        Perform authentication against the OTAS backend.
        Stores the returned project info on this client instance.

        Returns:
            self  (allows chaining: client = OtasClient(key).authenticate())
        """
        self._credentials = authenticate(self.sdk_key)
        return self

    @property
    def is_authenticated(self) -> bool:
        return self._credentials is not None

    @property
    def project_id(self) -> str | None:
        return (self._credentials or {}).get("project_id")

    @property
    def project_name(self) -> str | None:
        return (self._credentials or {}).get("project_name")

    @property
    def project_description(self) -> str | None:
        return (self._credentials or {}).get("project_description")

    def __repr__(self) -> str:
        if self.is_authenticated:
            return f"<OtasClient project='{self.project_name}' id='{self.project_id}'>"
        return "<OtasClient [unauthenticated]>"