from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
from dataclasses import dataclass
from typing import Mapping

import requests

from llama_index.tools.talordata_serp import TalordataSerpToolSpec


COMMON_PROXY_PORTS = (
    7890,
    7897,
    7891,
    7892,
    7893,
    1080,
    1081,
    10808,
    10809,
    9567,
    8080,
    8888,
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    result_count: int | None = None
    sample_title: str | None = None
    error_type: str | None = None
    error_status_code: int | None = None
    error_message: str | None = None


def _normalize_proxy_url(value: str) -> str | None:
    proxy = value.strip()
    if not proxy:
        return None
    if ";" in proxy:
        for part in proxy.split(";"):
            if "=" not in part:
                continue
            key, raw_value = part.split("=", 1)
            if key.strip().lower() in {"http", "https"}:
                proxy = raw_value.strip()
                break
    if not proxy:
        return None
    if "://" not in proxy:
        proxy = f"http://{proxy}"
    return proxy


def read_windows_proxy_server() -> str | None:
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-ItemProperty "
                    "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' "
                    "| Select-Object -ExpandProperty ProxyServer"
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = completed.stdout.strip()
    return value or None


def read_netstat_output() -> str:
    try:
        completed = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return completed.stdout


def local_listen_proxy_candidates(netstat_output: str | None = None) -> list[str]:
    if netstat_output is None:
        netstat_output = read_netstat_output()

    candidates: list[str] = []
    for line in netstat_output.splitlines():
        if "LISTENING" not in line:
            continue
        match = re.search(r"^\s*TCP\s+(\S+):(\d+)\s+\S+\s+LISTENING\s+\d+", line)
        if not match:
            continue
        host, port_text = match.groups()
        if host not in {"127.0.0.1", "0.0.0.0"}:
            continue
        port = int(port_text)
        if port < 1024:
            continue
        candidates.append(f"http://127.0.0.1:{port}")
    return candidates


def discover_proxy_candidates(
    *,
    env: Mapping[str, str] | None = None,
    registry_proxy: str | None = None,
    ports: tuple[int, ...] = COMMON_PROXY_PORTS,
    include_listeners: bool = False,
) -> list[str]:
    env = env or os.environ
    candidates: list[str] = []

    for key in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
        value = env.get(key)
        if value:
            proxy = _normalize_proxy_url(value)
            if proxy:
                candidates.append(proxy)

    if registry_proxy is None:
        registry_proxy = read_windows_proxy_server()
    if registry_proxy:
        proxy = _normalize_proxy_url(registry_proxy)
        if proxy:
            candidates.append(proxy)

    candidates.extend(f"http://127.0.0.1:{port}" for port in ports)
    if include_listeners:
        candidates.extend(local_listen_proxy_candidates())

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate not in seen:
            deduped.append(candidate)
            seen.add(candidate)
    return deduped


def with_proxy_environment(env: Mapping[str, str], proxy_url: str) -> dict[str, str]:
    updated = dict(env)
    updated["HTTP_PROXY"] = proxy_url
    updated["HTTPS_PROXY"] = proxy_url
    return updated


def can_connect_proxy(proxy_url: str, timeout: float = 0.5) -> bool:
    try:
        host_port = proxy_url.split("://", 1)[-1].split("/", 1)[0]
        host, port_text = host_port.rsplit(":", 1)
        with socket.create_connection((host, int(port_text)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def find_working_proxy(candidates: list[str]) -> str | None:
    for candidate in candidates:
        if can_connect_proxy(candidate):
            return candidate
    return None


def fetch_ip(proxy_url: str | None = None, timeout: int = 20) -> dict:
    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    response = requests.get("https://ipapi.co/json/", proxies=proxies, timeout=timeout)
    response.raise_for_status()
    return response.json()


def select_working_proxy(
    candidates: list[str],
    *,
    can_connect=can_connect_proxy,
    fetch_ip_func=fetch_ip,
) -> tuple[str | None, dict | None]:
    for candidate in candidates:
        if not can_connect(candidate):
            continue
        try:
            return candidate, fetch_ip_func(candidate)
        except Exception:
            continue
    return None, None


def select_working_proxy_lenient(
    proxy_url: str,
    *,
    can_connect=can_connect_proxy,
    fetch_ip_func=fetch_ip,
) -> tuple[str | None, dict | None]:
    if not can_connect(proxy_url):
        return None, None
    try:
        return proxy_url, fetch_ip_func(proxy_url)
    except Exception:
        return proxy_url, None


def summarize_payload(name: str, payload_text: str) -> CheckResult:
    payload = json.loads(payload_text)
    if "error" in payload:
        error = payload["error"]
        return CheckResult(
            name=name,
            ok=False,
            error_type=error.get("type"),
            error_status_code=error.get("status_code"),
            error_message=error.get("message"),
        )

    results = payload.get("results")
    if isinstance(results, list):
        sample_title = None
        if results:
            sample = results[0]
            sample_title = sample.get("title") or sample.get("alt") or sample.get("name")
        return CheckResult(
            name=name,
            ok=True,
            result_count=len(results),
            sample_title=sample_title,
        )

    return CheckResult(name=name, ok=True, result_count=None)


def is_mainland_china_block(result: CheckResult) -> bool:
    message = result.error_message or ""
    return "Not supported for use in mainland China" in message


def run_serp_checks(api_key: str) -> list[CheckResult]:
    tool = TalordataSerpToolSpec(api_key=api_key)
    checks = [
        (
            "search_engine",
            tool.search_engine(
                query="coffee",
                engine="google",
                country="us",
                language="en",
                num=3,
            ),
        ),
        (
            "image_search",
            tool.image_search(
                query="coffee",
                engine="bing_images",
                country="us",
                language="en",
                count=3,
            ),
        ),
        (
            "raw_serp_request",
            tool.raw_serp_request(
                engine="google",
                query="coffee",
                params_json=json.dumps({"num": 3, "country": "us", "language": "en"}),
            ),
        ),
    ]
    return [summarize_payload(name, payload) for name, payload in checks]


def print_result(result: CheckResult) -> None:
    print(f"[{result.name}] ok={result.ok}")
    if result.ok:
        print(f"  result_count={result.result_count}")
        if result.sample_title:
            print(f"  sample_title={result.sample_title}")
        return
    print(f"  error_type={result.error_type}")
    print(f"  error_status_code={result.error_status_code}")
    print(f"  error_message={result.error_message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Talordata SERP checks through a local proxy.")
    parser.add_argument("--api-key", default=os.environ.get("TALORDATA_SERP_API_KEY"))
    parser.add_argument("--proxy", default=None, help="Explicit proxy URL, for example http://127.0.0.1:7890")
    parser.add_argument("--scan-listeners", action="store_true", help="Also try every local listening TCP port.")
    parser.add_argument("--skip-serp", action="store_true", help="Only check proxy discovery and IP.")
    args = parser.parse_args(argv)

    candidates = [args.proxy] if args.proxy else discover_proxy_candidates(include_listeners=args.scan_listeners)
    candidates = [candidate for candidate in candidates if candidate]
    if args.proxy:
        proxy, ip_info = select_working_proxy_lenient(
            args.proxy,
            fetch_ip_func=lambda proxy_url: fetch_ip(proxy_url, timeout=5),
        )
    else:
        proxy, ip_info = select_working_proxy(
            candidates,
            fetch_ip_func=lambda proxy_url: fetch_ip(proxy_url, timeout=5),
        )
    if not proxy:
        print("No reachable local proxy found.")
        print("Tried:")
        for candidate in candidates:
            print(f"  {candidate}")
        return 2

    os.environ.update(with_proxy_environment(os.environ, proxy))
    print(f"proxy={proxy}")
    print(f"proxy_ip={ip_info.get('ip') if ip_info else None}")
    print(f"proxy_country={ip_info.get('country_name') if ip_info else None}")

    if args.skip_serp:
        return 0
    if not args.api_key:
        print("TALORDATA_SERP_API_KEY is required for SERP checks.")
        return 4

    results = run_serp_checks(args.api_key)
    for result in results:
        print_result(result)

    if any(is_mainland_china_block(result) for result in results):
        return 5
    return 0 if all(result.ok for result in results) else 6


if __name__ == "__main__":
    raise SystemExit(main())
