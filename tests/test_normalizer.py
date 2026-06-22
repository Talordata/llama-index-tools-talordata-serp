from llama_index.tools.talordata_serp.normalizer import normalize_image_results
from llama_index.tools.talordata_serp.normalizer import normalize_raw_payload
from llama_index.tools.talordata_serp.normalizer import normalize_web_results
from llama_index.tools.talordata_serp.normalizer import without_raw


def test_normalize_web_results_supports_organic_results():
    payload = {
        "organic_results": [
            {
                "title": "Coffee",
                "link": "https://example.com/coffee",
                "snippet": "Coffee article",
            }
        ]
    }

    result = normalize_web_results("coffee", "google", payload)

    assert result["query"] == "coffee"
    assert result["engine"] == "google"
    assert result["results"][0] == {
        "title": "Coffee",
        "link": "https://example.com/coffee",
        "snippet": "Coffee article",
        "source": "",
    }
    assert result["raw"] == payload


def test_normalize_web_results_supports_talordata_organic_key():
    payload = {
        "code": 0,
        "data": {
            "json": '{"organic":[{"title":"Coffee","url":"https://example.com/coffee","description":"Coffee article","domain":"Example"}]}'
        },
    }

    result = normalize_web_results("coffee", "google", payload)

    assert result["results"][0] == {
        "title": "Coffee",
        "link": "https://example.com/coffee",
        "snippet": "Coffee article",
        "source": "Example",
    }


def test_normalize_image_results_reads_nested_data_json_object():
    payload = {
        "code": 0,
        "task_id": "img-task",
        "data": {
            "json": {
                "images_results": [
                    {
                        "title": "Pizza image",
                        "link": "https://example.com/page",
                        "original": "https://example.com/pizza.jpg",
                    }
                ]
            }
        },
    }

    result = normalize_image_results("pizza", "google_images", payload)

    assert result["task_id"] == "img-task"
    assert result["status_code"] == 0
    assert result["results"][0]["image_url"] == "https://example.com/pizza.jpg"


def test_normalize_raw_payload_exposes_data_json():
    payload = {
        "code": 0,
        "task_id": "raw-task",
        "data": {
            "json": '{"answer_box":{"title":"Coffee"}}',
            "html": "<html><body><h1>Coffee</h1></body></html>",
        },
    }

    result = normalize_raw_payload("coffee", "google", payload)

    assert result["query"] == "coffee"
    assert result["engine"] == "google"
    assert result["data_json"] == {"answer_box": {"title": "Coffee"}}
    assert result["html_preview"] == "Coffee"
    assert result["raw"] == payload


def test_without_raw_removes_raw_payload():
    payload = {"raw": {"large": "payload"}, "results": [{"title": "A"}]}

    assert without_raw(payload) == {"results": [{"title": "A"}]}
