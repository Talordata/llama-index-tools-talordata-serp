import pytest
import responses

from llama_index.tools.talordata_serp.client import SerpApiError
from llama_index.tools.talordata_serp.client import SerpClient


ENDPOINT = "https://devserp.seboll.com/serp/v1/request"
PRODUCTION_ENDPOINT = "https://serpapi.talordata.net/serp/v1/request"


def test_default_serp_endpoint_uses_production_api():
    from llama_index.tools.talordata_serp.client import DEFAULT_SERP_ENDPOINT

    assert DEFAULT_SERP_ENDPOINT == PRODUCTION_ENDPOINT


@responses.activate
def test_serp_client_posts_form_encoded_request():
    responses.add(
        responses.POST,
        ENDPOINT,
        json={"organic_results": [{"title": "A", "link": "https://example.com/a"}]},
        status=200,
    )

    client = SerpClient(endpoint=ENDPOINT, api_key="sk_test")
    result = client.request({"engine": "google", "q": "coffee", "num": 3, "empty": ""})

    assert result == {"organic_results": [{"title": "A", "link": "https://example.com/a"}]}
    call = responses.calls[0].request
    assert call.headers["Authorization"] == "Bearer sk_test"
    assert call.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert call.headers["Origin"] == "Llamaindex"
    assert call.body == "engine=google&q=coffee&num=3&json=2"


def test_serp_client_rejects_empty_api_key():
    with pytest.raises(ValueError, match="SERP API key is required"):
        SerpClient(endpoint=ENDPOINT, api_key="")


@responses.activate
def test_serp_client_raises_api_error_for_non_2xx():
    responses.add(
        responses.POST,
        ENDPOINT,
        json={"error": "invalid api key"},
        status=401,
    )

    client = SerpClient(endpoint=ENDPOINT, api_key="sk_bad")

    with pytest.raises(SerpApiError) as exc:
        client.request({"engine": "google", "q": "coffee"})

    assert exc.value.status_code == 401
    assert "invalid api key" in str(exc.value)


@responses.activate
def test_serp_client_raises_api_error_for_business_error_payload():
    responses.add(
        responses.POST,
        ENDPOINT,
        json={"code": 401, "data": "API key authentication failed"},
        status=200,
    )

    client = SerpClient(endpoint=ENDPOINT, api_key="abc123")

    with pytest.raises(SerpApiError) as exc:
        client.request({"engine": "google", "q": "dify"})

    assert exc.value.status_code == 401
    assert "API key authentication failed" in str(exc.value)
