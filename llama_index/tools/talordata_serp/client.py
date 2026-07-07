from __future__ import annotations

import json
from typing import Any

import requests


DEFAULT_SERP_ENDPOINT = "https://serpapi.talordata.net/serp/v1/request"


class SerpApiError(RuntimeError):
    def __init__(self, status_code: int, message: str, payload: Any | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class SerpClient:
    def __init__(self, api_key: str, endpoint: str = DEFAULT_SERP_ENDPOINT, timeout: int = 60):
        api_key = (api_key or "").strip()
        endpoint = (endpoint or DEFAULT_SERP_ENDPOINT).strip()
        if not api_key:
            raise ValueError("SERP API key is required")
        if not endpoint:
            raise ValueError("SERP endpoint is required")

        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout

    def request(self, params: dict[str, Any]) -> dict[str, Any]:
        cleaned = self._clean_params(params)
        response = requests.post(
            self.endpoint,
            data=cleaned,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "Llamaindex",
            },
            timeout=self.timeout,
        )

        payload = self._parse_response(response)
        if response.status_code < 200 or response.status_code >= 300:
            message = self._error_message(payload, response.text)
            raise SerpApiError(response.status_code, message, payload)
        if not isinstance(payload, dict):
            raise SerpApiError(response.status_code, "SERP API returned a non-object JSON response", payload)
        business_error = self._business_error_code(payload)
        if business_error is not None:
            raise SerpApiError(business_error, self._error_message(payload, response.text), payload)
        return payload

    @staticmethod
    def _clean_params(params: dict[str, Any]) -> dict[str, str]:
        params = dict(params or {})
        params.setdefault("json", 2)
        cleaned: dict[str, str] = {}
        for key, value in params.items():
            if value is None or value == "":
                continue
            if isinstance(value, bool):
                cleaned[key] = "true" if value else "false"
            else:
                cleaned[key] = str(value)
        return cleaned

    @staticmethod
    def _parse_response(response: requests.Response) -> Any:
        if not response.text:
            return {}
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise SerpApiError(response.status_code, "SERP API returned invalid JSON", response.text) from exc

    @staticmethod
    def _error_message(payload: Any, fallback: str) -> str:
        if isinstance(payload, dict):
            for key in ("message", "error", "msg", "data"):
                value = payload.get(key)
                if value:
                    return str(value)
        return fallback or "SERP API request failed"

    @staticmethod
    def _business_error_code(payload: dict[str, Any]) -> int | None:
        code = payload.get("code")
        if code in (None, "", 0, "0", 200, "200"):
            return None
        try:
            return int(code)
        except (TypeError, ValueError):
            return 500
