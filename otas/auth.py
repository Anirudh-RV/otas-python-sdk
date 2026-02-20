import requests
from .exceptions import OtasAuthenticationError
from .constants import AUTHENTICATE_URL


def authenticate(sdk_key: str) -> dict:
    """
    Authenticate with the OTAS backend using the provided SDK key.

    Args:
        sdk_key: The OTAS SDK key (e.g. 'otas_PocKPi56xDI_...')

    Returns:
        A dict containing project info from the authentication response.

    Raises:
        OtasAuthenticationError: If authentication fails.
    """
    headers = {"X-OTAS-SDK-KEY": sdk_key}

    try:
        response = requests.post(AUTHENTICATE_URL, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise OtasAuthenticationError(f"Failed to reach OTAS authentication endpoint: {e}") from e

    data = response.json()

    if data.get("status") != 1:
        description = data.get("status_description", "unknown error")
        raise OtasAuthenticationError(f"OTAS authentication failed: {description}")

    project_info = data.get("response", {}).get("project", {})

    return {
        "project_id": project_info.get("id"),
        "project_name": project_info.get("name"),
        "project_description": project_info.get("description"),
        "sdk_key": sdk_key,
    }