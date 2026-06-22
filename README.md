# LlamaIndex Tools Integration: Talordata SERP

**LlamaIndex Tools Integration: Talordata SERP**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)





This package connects LlamaIndex agents to the Talordata SERP API for live web, image, and news search.

It exposes a `TalordataSerpToolSpec` that can be converted into LlamaIndex tools with `to_tool_list()`.

## Installation

Install from PyPI:

```powershell
python -m pip install llama-index llama-index-core llama-index-tools-talordata-serp
```

For local development from source:

```powershell
python -m pip install -e ".[dev]"
```

For the OpenAI agent example below, also install the optional OpenAI LLM integration:

```powershell
python -m pip install -e ".[dev,openai]"
```

## Authentication

Use a Talordata SERP API key:

```text
sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Do not use a Talordata dashboard login JWT. Dashboard JWT tokens are for dashboard APIs, while this package calls the SERP request API with `Authorization: Bearer <SERP_API_KEY>`.

You can pass the API key directly:

```python
from llama_index.tools.talordata_serp import TalordataSerpToolSpec

tool_spec = TalordataSerpToolSpec(api_key="sk_xxx")
```

Or read it from an environment variable in your application code.

## Basic Usage

```python
from llama_index.tools.talordata_serp import TalordataSerpToolSpec

tool_spec = TalordataSerpToolSpec(api_key="sk_xxx")
tools = tool_spec.to_tool_list()
```

## Direct ToolSpec Calls

```python
import json

from llama_index.tools.talordata_serp import TalordataSerpToolSpec

tool_spec = TalordataSerpToolSpec(api_key="sk_xxx")

result = tool_spec.search_engine(
    query="latest AI search trends",
    engine="google",
    country="us",
    language="en",
    num=5,
)

print(json.loads(result))
```

## Agent Usage

This example requires the `openai` extra:

```powershell
python -m pip install "llama-index-llms-openai>=0.3.0"
```

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from llama_index.tools.talordata_serp import TalordataSerpToolSpec

tool_spec = TalordataSerpToolSpec(api_key="sk_xxx")

agent = FunctionAgent(
    tools=tool_spec.to_tool_list(),
    llm=OpenAI(model="gpt-4.1"),
)
```

## Tools

### `search_engine`

Search Google, Bing, Yandex, or DuckDuckGo and return normalized web results.

```python
result = tool_spec.search_engine(
    query="coffee",
    engine="google",
    country="us",
    language="en",
    num=3,
)
```

### `image_search`

Search Bing Images or Google Images and return normalized image results.

```python
result = tool_spec.image_search(
    query="coffee",
    engine="bing_images",
    country="us",
    language="en",
    count=3,
)
```

### `news_search`

Search Google News or Bing News and return normalized news-style results.

```python
result = tool_spec.news_search(
    query="markets",
    engine="google_news",
    country="us",
    language="en",
)
```

### `raw_serp_request`

Pass an engine and extra JSON parameters directly to the Talordata SERP API. Use this when you need engine-specific parameters that are not exposed by the normalized helpers.

```python
result = tool_spec.raw_serp_request(
    engine="google",
    query="coffee",
    params_json='{"num": 3, "country": "us", "language": "en"}',
)
```

## Response Shape

Normal search tools return a JSON string with this shape:

```json
{
  "query": "coffee",
  "engine": "google",
  "results": [
    {
      "title": "Coffee",
      "link": "https://example.com",
      "snippet": "Coffee article",
      "source": "Example"
    }
  ]
}
```

Agent-friendly errors are returned as JSON strings:

```json
{
  "error": {
    "type": "SerpApiError",
    "status_code": 401,
    "message": "API key authentication failed"
  }
}
```

Set `include_raw=True` on normal tools when the caller needs the full upstream payload.

## Network Troubleshooting

If your command line cannot access the SERP API directly, run the manual checker through a local Clash/SSRDOG proxy without enabling a global system proxy:

```powershell
$env:TALORDATA_SERP_API_KEY="sk_xxx"
python scripts/manual_serp_proxy_check.py --proxy http://127.0.0.1:7890
```

If you do not know the local proxy port, try:

```powershell
python scripts/manual_serp_proxy_check.py --skip-serp
python scripts/manual_serp_proxy_check.py --skip-serp --scan-listeners
```

The script only sets proxy variables inside its own Python process. It does not enable or change the system-wide proxy.

## Development

```powershell
python -m pip install -e ".[dev]"
python -m pytest -v
```

Build release artifacts:

```powershell
python -m build
```

## First-Version Boundary

The SERP client and normalizers are copied from the Dify plugin for the first LlamaIndex version. The shared SDK extraction is a separate follow-up once the LlamaIndex package shape is validated.


## 🎁 Get Started for Free

Try TalorData SERP API with **1,000 free searches** and start building AI agents, SEO tools, and search-driven applications today.

- No infrastructure to manage
- Multi-engine search access
- Real-time structured results
- Developer-friendly integration

👉 [Start Free](https://talordata.com/?campaignid=hiy46bmdwF990Hqs&utm_source=Github29&utm_term=Github29)

---

## 🤝 Connect With Us

Have questions or want to collaborate? Reach out through any of the following channels:

- 📧 **Email:** [support@talordata.com](mailto:support@talordata.com)  
- 🌐 **Website:** [https://talordata.com](	https://talordata.com/?campaignid=hiy46bmdwF990Hqs&utm_source=Github29&utm_term=Github29)   
- 📱 **WhatsApp:** [+852 5628 3471](https://wa.me/85256283471)  
- 💼 **LinkedIn:** [TalorData](linkedin.com/company/talordata)

---

> **TalorData empowers developers and AI agents with fast, reliable search-data access through a single multi-engine SERP API.**