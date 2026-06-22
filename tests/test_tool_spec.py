import json

import responses

from llama_index.tools.talordata_serp import TalordataSerpToolSpec


ENDPOINT = "https://devserp.seboll.com/serp/v1/request"


@responses.activate
def test_search_engine_maps_google_params_and_hides_raw_by_default():
    responses.add(
        responses.POST,
        ENDPOINT,
        json={"organic_results": [{"title": "Coffee", "link": "https://example.com", "snippet": "Article"}]},
        status=200,
    )

    tool_spec = TalordataSerpToolSpec(api_key="sk_test", endpoint=ENDPOINT)
    payload = json.loads(tool_spec.search_engine(query="coffee", engine="google", country="us", language="en", num=5))

    assert payload["query"] == "coffee"
    assert payload["engine"] == "google"
    assert payload["results"][0]["title"] == "Coffee"
    assert "raw" not in payload
    assert responses.calls[0].request.body == "engine=google&q=coffee&gl=us&hl=en&num=5&no_cache=false&json=2"


@responses.activate
def test_image_search_maps_bing_params_and_can_include_raw():
    responses.add(
        responses.POST,
        ENDPOINT,
        json={"images_results": [{"title": "Coffee", "original": "https://example.com/coffee.jpg"}]},
        status=200,
    )

    tool_spec = TalordataSerpToolSpec(api_key="sk_test", endpoint=ENDPOINT)
    payload = json.loads(
        tool_spec.image_search(
            query="coffee",
            engine="bing_images",
            country="us",
            language="en",
            count=3,
            include_raw=True,
        )
    )

    assert payload["engine"] == "bing_images"
    assert payload["results"][0]["image_url"] == "https://example.com/coffee.jpg"
    assert payload["raw"] == {"images_results": [{"title": "Coffee", "original": "https://example.com/coffee.jpg"}]}
    assert responses.calls[0].request.body == "engine=bing_images&q=coffee&cc=us&setlang=en&count=3&no_cache=false&json=2"


@responses.activate
def test_news_search_uses_news_engine():
    responses.add(
        responses.POST,
        ENDPOINT,
        json={"news_results": [{"title": "Market news", "link": "https://example.com/news"}]},
        status=200,
    )

    tool_spec = TalordataSerpToolSpec(api_key="sk_test", endpoint=ENDPOINT)
    payload = json.loads(tool_spec.news_search(query="markets", engine="google_news", country="us", language="en"))

    assert payload["engine"] == "google_news"
    assert payload["results"][0]["title"] == "Market news"


@responses.activate
def test_raw_serp_request_merges_params_json():
    responses.add(
        responses.POST,
        ENDPOINT,
        json={"answer_box": {"title": "Coffee"}},
        status=200,
    )

    tool_spec = TalordataSerpToolSpec(api_key="sk_test", endpoint=ENDPOINT)
    payload = json.loads(
        tool_spec.raw_serp_request(
            engine="google",
            query="coffee",
            params_json='{"gl":"us","hl":"en","num":2}',
        )
    )

    assert payload["engine"] == "google"
    assert payload["query"] == "coffee"
    assert payload["raw"] == {"answer_box": {"title": "Coffee"}}
    assert responses.calls[0].request.body == "engine=google&q=coffee&gl=us&hl=en&num=2&json=2"


def test_raw_serp_request_rejects_invalid_params_json():
    tool_spec = TalordataSerpToolSpec(api_key="sk_test", endpoint=ENDPOINT)

    payload = json.loads(tool_spec.raw_serp_request(engine="google", query="coffee", params_json="{bad"))

    assert payload == {
        "error": {
            "type": "ValueError",
            "message": "params_json is invalid JSON",
        }
    }


@responses.activate
def test_tool_methods_return_agent_friendly_error_json():
    responses.add(
        responses.POST,
        ENDPOINT,
        json={"code": 401, "data": "API key authentication failed"},
        status=200,
    )

    tool_spec = TalordataSerpToolSpec(api_key="sk_bad", endpoint=ENDPOINT)
    payload = json.loads(tool_spec.search_engine(query="coffee"))

    assert payload == {
        "error": {
            "type": "SerpApiError",
            "status_code": 401,
            "message": "API key authentication failed",
        }
    }


def test_to_tool_list_exposes_four_tools():
    tool_spec = TalordataSerpToolSpec(api_key="sk_test", endpoint=ENDPOINT)
    tools = tool_spec.to_tool_list()

    assert [tool.metadata.name for tool in tools] == [
        "search_engine",
        "image_search",
        "news_search",
        "raw_serp_request",
    ]
