from __future__ import annotations

import json
import re
from typing import Any


def normalize_image_results(query: str, engine: str, payload: dict[str, Any]) -> dict[str, Any]:
    unwrapped = unwrap_payload(payload)
    source = unwrapped["data_json"] if isinstance(unwrapped["data_json"], dict) else payload
    source_items = _first_list(source, ("images_results", "inline_images", "image_results"))
    results = []
    for item in source_items:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": _text(item, "title", "name"),
                "link": _text(item, "link", "source_link", "original_context_url"),
                "image_url": _text(item, "original", "image", "image_url", "thumbnail"),
                "thumbnail_url": _text(item, "thumbnail", "thumbnail_url", "image"),
                "source": _text(item, "source", "domain"),
            }
        )

    return {
        "query": query,
        "engine": engine,
        "results": results,
        **response_metadata(unwrapped),
        "raw": payload,
    }


def normalize_web_results(query: str, engine: str, payload: dict[str, Any]) -> dict[str, Any]:
    unwrapped = unwrap_payload(payload)
    source = unwrapped["data_json"] if isinstance(unwrapped["data_json"], dict) else payload
    source_items = _first_list(source, ("organic_results", "organic", "results", "news_results"))
    results = []
    for item in source_items:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": _text(item, "title", "name"),
                "link": _text(item, "link", "url"),
                "snippet": _text(item, "snippet", "description", "summary"),
                "source": _text(item, "source", "domain"),
            }
        )

    return {
        "query": query,
        "engine": engine,
        "results": results,
        **response_metadata(unwrapped),
        "raw": payload,
    }


def normalize_raw_payload(query: str, engine: str, payload: dict[str, Any]) -> dict[str, Any]:
    unwrapped = unwrap_payload(payload)
    return {
        "query": query,
        "engine": engine,
        **response_metadata(unwrapped, include_data_json=True),
        "raw": payload,
    }


def without_raw(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "raw"}


def unwrap_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    html = ""
    data_json: Any = None

    if isinstance(data, dict):
        html = _string(data.get("html"))
        data_json = _parse_data_json(data.get("json"))
    elif isinstance(data, str):
        data_json = _parse_data_json(data)

    return {
        "status_code": payload.get("code") if isinstance(payload, dict) else None,
        "task_id": payload.get("task_id") if isinstance(payload, dict) else None,
        "html": html,
        "html_preview": html_preview(html),
        "data_json": data_json,
    }


def response_metadata(unwrapped: dict[str, Any], include_data_json: bool = False) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for key in ("status_code", "task_id", "html", "html_preview"):
        value = unwrapped.get(key)
        if value not in (None, ""):
            metadata[key] = value
    if include_data_json and unwrapped.get("data_json") not in (None, ""):
        metadata["data_json"] = unwrapped["data_json"]
    return metadata


def html_preview(html: str, max_length: int = 500) -> str:
    if not html:
        return ""
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_length]


def _first_list(payload: dict[str, Any], keys: tuple[str, ...]) -> list[Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _text(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None:
            return str(value)
    return ""


def _parse_data_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _string(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
