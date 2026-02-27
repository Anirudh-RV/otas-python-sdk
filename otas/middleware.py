import os
import json
import time
from typing import Dict, Any, Set

import requests

from django.utils import timezone
from django.http import StreamingHttpResponse

from .client import OtasClient
from .exceptions import OtasConfigurationError
from .logger import logger
from .constants import OTAS_LOG_ENDPOINT, MAX_BODY_SIZE
import threading
from django.core.signals import got_request_exception


class OtasMiddleware:

    DEFAULT_SENSITIVE_HEADERS: Set[str] = {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "proxy-authorization",
    }

    # ------------------------------------------------------------------ #
    # Initialization
    # ------------------------------------------------------------------ #

    def __init__(self, get_response, *args, **kwargs):
        self.get_response = get_response
        self.client = self._initialize_client()
        self.sensitive_headers = self._load_sensitive_headers()
        self._local = threading.local()
        got_request_exception.connect(self._on_exception)

    def _initialize_client(self) -> OtasClient:
        sdk_key = os.environ.get("OTAS_SDK_KEY")
        if not sdk_key:
            raise OtasConfigurationError(
                "OTAS_SDK_KEY environment variable is not set."
            )

        client = OtasClient(sdk_key)
        client.authenticate()

        logger.info(
            "[OTAS] Initialised project '%s' (id: %s)",
            client.project_name,
            client.project_id,
        )
        return client

    def _load_sensitive_headers(self) -> Set[str]:
        env_headers = os.environ.get("OTAS_SENSITIVE_HEADERS", "")
        parsed = {
            h.strip().lower()
            for h in env_headers.split(",")
            if h.strip()
        }
        return self.DEFAULT_SENSITIVE_HEADERS.union(parsed)
    
    def _on_exception(self, sender, request, **kwargs):
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        self._local.exception = exc_value

    # ------------------------------------------------------------------ #
    # Request lifecycle
    # ------------------------------------------------------------------ #

    def __call__(self, request):
        request._otas_start_time = time.perf_counter()
        request._otas_request_data = self._capture_request(request)
        self._local.exception = None  # reset for this request

        response = self.get_response(request)

        latency_ms = (time.perf_counter() - request._otas_start_time) * 1000
        response_data = self._capture_response(response)

        # Grab exception captured via signal
        captured_exception = self._local.exception
        
        if captured_exception:
            response_data["response_body"] = ""
            response_data["response_size_bytes"] = 0

        payload = self._build_payload(
            request=request,
            response_data=response_data,
            latency_ms=latency_ms,
            error=repr(captured_exception) if captured_exception else None,
        )
        self._send_to_otas(payload)
        return response
    

    # ------------------------------------------------------------------ #
    # Capture logic
    # ------------------------------------------------------------------ #

    def _capture_request(self, request) -> Dict[str, Any]:
        body = b""
        content_type = request.content_type

        try:
            if self._should_capture_body(content_type):
                body = request.body
        except Exception:
            pass

        body = self._truncate(body)

        agent_session_token = request.META.get(
            "HTTP_X_OTAS_AGENT_SESSION_TOKEN", ""
        )

        headers = self._extract_request_headers(request)

        return {
            "method": request.method,
            "path": request.path,
            "query_params": json.dumps(dict(request.GET)),
            "post_data": json.dumps(dict(request.POST)),
            "request_headers": json.dumps(headers),
            "request_body": body.decode(errors="ignore"),
            "request_size_bytes": len(body),
            "request_content_type": content_type,
            "agent_session_token": agent_session_token,
        }

    def _capture_response(self, response) -> Dict[str, Any]:
        body = b""
        headers = dict(response.items())

        if isinstance(response, StreamingHttpResponse):
            body = b"[STREAMING_RESPONSE]"
        elif hasattr(response, "content"):
            body = response.content

        body = self._truncate(body)
        headers = self._redact_headers(headers)

        return {
            "status_code": response.status_code,
            "response_headers": json.dumps(headers),
            "response_body": body.decode(errors="ignore"),
            "response_size_bytes": len(body),
            "response_content_type": headers.get("Content-Type"),
        }

    # ------------------------------------------------------------------ #
    # Payload builder
    # ------------------------------------------------------------------ #

    def _build_payload(self, request, response_data, latency_ms, error):
        request_data = getattr(request, "_otas_request_data", {})

        return {
            "project_id": self.client.project_id,
            "path": request_data.get("path"),
            "method": request_data.get("method"),
            "status_code": response_data.get("status_code"),
            "latency_ms": latency_ms,
            "request_size_bytes": request_data.get("request_size_bytes"),
            "response_size_bytes": response_data.get("response_size_bytes"),
            "request_headers": request_data.get("request_headers"),
            "request_body": request_data.get("request_body"),
            "query_params": request_data.get("query_params"),
            "post_data": request_data.get("post_data"),
            "response_headers": response_data.get("response_headers"),
            "response_body": response_data.get("response_body"),
            "request_content_type": request_data.get("request_content_type"),
            "response_content_type": response_data.get("response_content_type"),
            "custom_properties": {},
            "error": error or "",
            "metadata": {},
            "agent_session_token": request_data.get("agent_session_token"),
        }

    # ------------------------------------------------------------------ #
    # OTAS sending logic (synchronous, 1 event per request)
    # ------------------------------------------------------------------ #

    def _send_to_otas(self, payload: Dict[str, Any]) -> None:
        try:
            agent_session_token = payload.pop("agent_session_token", "")

            headers = {
                "Content-Type": "application/json",
                "X-OTAS-SDK-KEY": self.client.sdk_key,
            }

            if agent_session_token:
                headers["X-OTAS-AGENT-SESSION-TOKEN"] = agent_session_token

            response = requests.post(
                OTAS_LOG_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=2,  # prevent blocking app too long
            )

            if response.status_code >= 400:
                logger.warning(
                    "[OTAS] Failed to send event (%s): %s",
                    response.status_code,
                    response.text,
                )

        except Exception as exc:
            # Never break the user application
            logger.exception("[OTAS] Error sending event: %s", exc)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _extract_request_headers(self, request) -> Dict[str, str]:
        headers = {}

        for key, value in request.META.items():
            if key.startswith("HTTP_"):
                header_name = (
                    key.replace("HTTP_", "")
                    .replace("_", "-")
                    .lower()
                )
                headers[header_name] = value

        return self._redact_headers(headers)

    def _redact_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        redacted = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = value
        return redacted

    def _truncate(self, body: bytes) -> bytes:
        return body[:MAX_BODY_SIZE] if len(body) > MAX_BODY_SIZE else body

    def _should_capture_body(self, content_type: str | None) -> bool:
        if not content_type:
            return False

        content_type = content_type.lower()

        if "multipart/form-data" in content_type:
            return False
        if "application/octet-stream" in content_type:
            return False

        return True