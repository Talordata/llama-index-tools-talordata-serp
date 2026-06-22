from __future__ import annotations

import json
from typing import Any
from typing import Literal
from typing import Optional
from typing import Type

from llama_index.core.tools.tool_spec.base import BaseToolSpec
from pydantic import BaseModel
from pydantic import Field

from llama_index.tools.talordata_serp.client import DEFAULT_SERP_ENDPOINT
from llama_index.tools.talordata_serp.client import SerpApiError
from llama_index.tools.talordata_serp.client import SerpClient
from llama_index.tools.talordata_serp.normalizer import normalize_image_results
from llama_index.tools.talordata_serp.normalizer import normalize_raw_payload
from llama_index.tools.talordata_serp.normalizer import normalize_web_results
from llama_index.tools.talordata_serp.normalizer import without_raw


class SearchEngineInput(BaseModel):
    query: str = Field(..., description="Search query.")
    engine: Literal["google", "bing", "yandex", "duckduckgo", "google_web"] = Field(
        default="google",
        description="Search engine to call.",
    )
    country: str = Field(default="us", description="Country code, such as us, gb, or cn.")
    language: str = Field(default="en", description="Language code, such as en or zh-cn.")
    num: int = Field(default=10, ge=1, le=100, description="Number of results to request.")
    include_raw: bool = Field(default=False, description="Include the raw SERP API payload in the response.")
    no_cache: bool = Field(default=False, description="Bypass upstream cache when supported.")
    params_json: str = Field(default="", description="JSON object with additional SERP parameters.")


class ImageSearchInput(BaseModel):
    query: str = Field(..., description="Image search query.")
    engine: Literal["bing_images", "google_images"] = Field(default="bing_images", description="Image search engine.")
    country: str = Field(default="us", description="Country code, such as us, gb, or cn.")
    language: str = Field(default="en", description="Language code, such as en or zh-cn.")
    count: int = Field(default=10, ge=1, le=100, description="Number of image results to request.")
    include_raw: bool = Field(default=False, description="Include the raw SERP API payload in the response.")
    no_cache: bool = Field(default=False, description="Bypass upstream cache when supported.")
    params_json: str = Field(default="", description="JSON object with additional SERP parameters.")


class NewsSearchInput(BaseModel):
    query: str = Field(..., description="News search query.")
    engine: Literal["google_news", "bing_news"] = Field(default="google_news", description="News search engine.")
    country: str = Field(default="us", description="Country code, such as us, gb, or cn.")
    language: str = Field(default="en", description="Language code, such as en or zh-cn.")
    num: int = Field(default=10, ge=1, le=100, description="Number of news results to request.")
    include_raw: bool = Field(default=False, description="Include the raw SERP API payload in the response.")
    no_cache: bool = Field(default=False, description="Bypass upstream cache when supported.")
    params_json: str = Field(default="", description="JSON object with additional SERP parameters.")


class RawSerpRequestInput(BaseModel):
    engine: str = Field(..., description="SERP engine name, such as google, bing_images, or google_news.")
    query: str = Field(default="", description="Optional search query. Sent as q when provided.")
    params_json: str = Field(default="", description="JSON object with additional SERP parameters.")


class TalordataSerpToolSpec(BaseToolSpec):
    """Talordata SERP tool spec for LlamaIndex agents."""

    spec_functions = ["search_engine", "image_search", "news_search", "raw_serp_request"]

    def __init__(
        self,
        api_key: str,
        endpoint: str = DEFAULT_SERP_ENDPOINT,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout

    def get_fn_schema_from_fn_name(
        self,
        fn_name: str,
        spec_functions: Optional[list[str]] = None,
    ) -> Optional[Type[BaseModel]]:
        schema_by_name: dict[str, Type[BaseModel]] = {
            "search_engine": SearchEngineInput,
            "image_search": ImageSearchInput,
            "news_search": NewsSearchInput,
            "raw_serp_request": RawSerpRequestInput,
        }
        return schema_by_name.get(fn_name)

    def search_engine(
        self,
        query: str,
        engine: str = "google",
        country: str = "us",
        language: str = "en",
        num: int = 10,
        include_raw: bool = False,
        no_cache: bool = False,
        params_json: str = "",
    ) -> str:
        """Search Google, Bing, Yandex, or DuckDuckGo through Talordata SERP API."""
        try:
            extra_params = _parse_params_json(params_json)
        except ValueError as exc:
            return _value_error_json(exc)
        params = {"engine": engine, "q": query}
        if engine == "bing":
            params.update({"cc": country, "setlang": language, "count": num})
        else:
            params.update({"gl": country, "hl": language, "num": num})
        params["no_cache"] = no_cache
        params.update(extra_params)
        return self._request_json(params, "web", query, engine, include_raw)

    def image_search(
        self,
        query: str,
        engine: str = "bing_images",
        country: str = "us",
        language: str = "en",
        count: int = 10,
        include_raw: bool = False,
        no_cache: bool = False,
        params_json: str = "",
    ) -> str:
        """Search images through Talordata SERP API."""
        try:
            extra_params = _parse_params_json(params_json)
        except ValueError as exc:
            return _value_error_json(exc)
        params = {"engine": engine, "q": query}
        if engine == "bing_images":
            params.update({"cc": country, "setlang": language, "count": count})
        else:
            params.update({"gl": country, "hl": language, "num": count})
        params["no_cache"] = no_cache
        params.update(extra_params)
        return self._request_json(params, "image", query, engine, include_raw)

    def news_search(
        self,
        query: str,
        engine: str = "google_news",
        country: str = "us",
        language: str = "en",
        num: int = 10,
        include_raw: bool = False,
        no_cache: bool = False,
        params_json: str = "",
    ) -> str:
        """Search news through Talordata SERP API."""
        try:
            extra_params = _parse_params_json(params_json)
        except ValueError as exc:
            return _value_error_json(exc)
        params = {"engine": engine, "q": query}
        if engine == "bing_news":
            params.update({"cc": country, "setlang": language, "count": num})
        else:
            params.update({"gl": country, "hl": language, "num": num})
        params["no_cache"] = no_cache
        params.update(extra_params)
        return self._request_json(params, "web", query, engine, include_raw)

    def raw_serp_request(
        self,
        engine: str,
        query: str = "",
        params_json: str = "",
    ) -> str:
        """Send a raw SERP request with an engine and a JSON object of extra parameters."""
        try:
            extra_params = _parse_params_json(params_json)
        except ValueError as exc:
            return _value_error_json(exc)
        params: dict[str, Any] = {"engine": engine}
        if query:
            params["q"] = query
        params.update(extra_params)
        params["engine"] = engine
        if query:
            params["q"] = query
        return self._request_json(params, "raw", query, engine, include_raw=True)

    def _request_json(
        self,
        params: dict[str, Any],
        result_type: str,
        query: str,
        engine: str,
        include_raw: bool,
    ) -> str:
        try:
            payload = SerpClient(api_key=self.api_key, endpoint=self.endpoint, timeout=self.timeout).request(params)
        except SerpApiError as exc:
            return _json_dumps(
                {
                    "error": {
                        "type": "SerpApiError",
                        "status_code": exc.status_code,
                        "message": str(exc),
                    }
                }
            )

        if result_type == "image":
            normalized = normalize_image_results(query, engine, payload)
        elif result_type == "web":
            normalized = normalize_web_results(query, engine, payload)
        else:
            normalized = normalize_raw_payload(query, engine, payload)

        if not include_raw:
            normalized = without_raw(normalized)
        return _json_dumps(normalized)


def _parse_params_json(value: str) -> dict[str, Any]:
    raw = str(value or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("params_json is invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("params_json must be a JSON object")
    return parsed


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _value_error_json(exc: ValueError) -> str:
    return _json_dumps(
        {
            "error": {
                "type": "ValueError",
                "message": str(exc),
            }
        }
    )
