UASAM_BASE_URL = "http://localhost:8000/"
BRAIN_BASE_URL = "http://localhost:8002/"
AUTHENTICATE_URL = UASAM_BASE_URL + "api/project/v1/sdk/backend/key/authenticate/"
OTAS_LOG_ENDPOINT = BRAIN_BASE_URL + "/api/v1/backend/log/sdk/"
MAX_BODY_SIZE = 1024 * 100  # 100KB cap