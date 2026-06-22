import json

from llama_index.tools.talordata_serp.manual_check import CheckResult
from llama_index.tools.talordata_serp.manual_check import discover_proxy_candidates
from llama_index.tools.talordata_serp.manual_check import is_mainland_china_block
from llama_index.tools.talordata_serp.manual_check import local_listen_proxy_candidates
from llama_index.tools.talordata_serp.manual_check import select_working_proxy
from llama_index.tools.talordata_serp.manual_check import select_working_proxy_lenient
from llama_index.tools.talordata_serp.manual_check import summarize_payload
from llama_index.tools.talordata_serp.manual_check import with_proxy_environment


def test_discover_proxy_candidates_prefers_explicit_environment():
    env = {
        "HTTPS_PROXY": "http://127.0.0.1:7897",
        "HTTP_PROXY": "http://127.0.0.1:7890",
    }

    candidates = discover_proxy_candidates(env=env, registry_proxy=None)

    assert candidates[:2] == ["http://127.0.0.1:7897", "http://127.0.0.1:7890"]
    assert len(candidates) == len(set(candidates))


def test_discover_proxy_candidates_accepts_windows_proxy_server():
    candidates = discover_proxy_candidates(env={}, registry_proxy="127.0.0.1:9567")

    assert candidates[0] == "http://127.0.0.1:9567"


def test_discover_proxy_candidates_can_skip_netstat_scan():
    candidates = discover_proxy_candidates(env={}, registry_proxy=None, include_listeners=False)

    assert "http://127.0.0.1:7890" in candidates
    assert all(not candidate.endswith(":3000") for candidate in candidates)


def test_local_listen_proxy_candidates_parses_netstat_output():
    output = """
  TCP    127.0.0.1:37600        0.0.0.0:0              LISTENING       30500
  TCP    0.0.0.0:8848           0.0.0.0:0              LISTENING       28616
  TCP    [::]:135               [::]:0                 LISTENING       1216
"""

    candidates = local_listen_proxy_candidates(output)

    assert candidates == ["http://127.0.0.1:37600", "http://127.0.0.1:8848"]


def test_with_proxy_environment_sets_only_current_mapping():
    env = {"TALORDATA_SERP_API_KEY": "secret"}

    updated = with_proxy_environment(env, "http://127.0.0.1:7890")

    assert updated["HTTP_PROXY"] == "http://127.0.0.1:7890"
    assert updated["HTTPS_PROXY"] == "http://127.0.0.1:7890"
    assert env == {"TALORDATA_SERP_API_KEY": "secret"}


def test_select_working_proxy_requires_ip_check_success():
    calls = []

    def fake_fetch_ip(proxy_url):
        calls.append(proxy_url)
        if proxy_url.endswith(":3000"):
            raise RuntimeError("not a proxy")
        return {"ip": "8.8.8.8", "country_name": "United States"}

    proxy, ip_info = select_working_proxy(
        ["http://127.0.0.1:3000", "http://127.0.0.1:7890"],
        can_connect=lambda proxy_url: True,
        fetch_ip_func=fake_fetch_ip,
    )

    assert proxy == "http://127.0.0.1:7890"
    assert ip_info == {"ip": "8.8.8.8", "country_name": "United States"}
    assert calls == ["http://127.0.0.1:3000", "http://127.0.0.1:7890"]


def test_select_working_proxy_lenient_accepts_reachable_explicit_proxy():
    proxy, ip_info = select_working_proxy_lenient(
        "http://127.0.0.1:7890",
        can_connect=lambda proxy_url: True,
        fetch_ip_func=lambda proxy_url: (_ for _ in ()).throw(RuntimeError("ip check failed")),
    )

    assert proxy == "http://127.0.0.1:7890"
    assert ip_info is None


def test_summarize_payload_reports_result_count_and_sample_title():
    payload = json.dumps(
        {
            "engine": "google",
            "query": "coffee",
            "results": [{"title": "Coffee result", "url": "https://example.com"}],
        }
    )

    summary = summarize_payload("search_engine", payload)

    assert summary == CheckResult(
        name="search_engine",
        ok=True,
        result_count=1,
        sample_title="Coffee result",
    )


def test_summarize_payload_reports_agent_error_json():
    payload = json.dumps(
        {
            "error": {
                "type": "SerpApiError",
                "status_code": 400,
                "message": "Not supported for use in mainland China:1.2.3.4",
            }
        }
    )

    summary = summarize_payload("search_engine", payload)

    assert summary.ok is False
    assert summary.error_type == "SerpApiError"
    assert summary.error_status_code == 400
    assert summary.error_message == "Not supported for use in mainland China:1.2.3.4"
    assert is_mainland_china_block(summary)
