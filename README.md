**LlamaIndex integration for TalorData SERP API**

[**TalorData**](https://www.talordata.com/serp-api/llamaindex?campaignid=iiJFnZLYEox652MG&utm_source=LlamaIndex&utm_term=LlamaIndex) helps developers and AI applications connect to real-time, structured, and reliable search data through a single SERP API. With support for Google, Bing, News, Images, Shopping, Maps, Scholar, Trends, and more, TalorData makes it easier to build AI agents, search copilots, SEO workflows, and data-driven automations powered by live search results.

The llama-index-tools-talordata-serp package brings TalorData’s real-time search capabilities into LlamaIndex, so you can add live search, engine inspection, request history, and usage analytics directly to your LLM workflows and AI agent systems.

**Overview**

llama-index-tools-talordata-serp provides LlamaIndex tools for [TalorData](https://www.talordata.com/serp-api/llamaindex?campaignid=iiJFnZLYEox652MG&utm_source=LlamaIndex&utm_term=LlamaIndex) SERP API, enabling your AI agents to:

*   **Search** - Query search engines with geo-targeting and language customization
    
*   **Inspect engines** - Discover supported engines and engine-specific parameters
    
*   **Query history** - Fetch SERP request history with filters
    
*   **View statistics** - Retrieve usage statistics by date range and engine
    

## Installation

Install from PyPI:

```plaintext
python -m pip install llama-index-tools-talordata-serp
```

## Authentication

### 1. Get your API key

Sign up at [TalorData](https://www.talordata.com/serp-api/llamaindex?campaignid=iiJFnZLYEox652MG&utm_source=LlamaIndex&utm_term=LlamaIndex) and get your API key from the dashboard.

### 2.Use a Talordata SERP API key:

```plaintext
sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Do not use a Talordata dashboard login JWT. Dashboard JWT tokens are for dashboard APIs, while this package calls the SERP request API with `Authorization: Bearer <SERP_API_KEY>`.

### 3.You can pass the API key directly:

```plaintext
from llama_index.tools.talordata_serp import TalordataSerpToolSpec

tool_spec = TalordataSerpToolSpec(api_key="sk_xxx")
```

Or read it from an environment variable in your application code.

## Basic Usage

```plaintext
from llama_index.tools.talordata_serp import TalordataSerpToolSpec

tool_spec = TalordataSerpToolSpec(api_key="sk_xxx")
tools = tool_spec.to_tool_list()
```

## Direct ToolSpec Calls

```plaintext
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

## Agent Usage

This example requires the `openai` extra:

```plaintext
python -m pip install "llama-index-llms-openai>=0.3.0"
```
```plaintext
import asyncio

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from llama_index.tools.talordata_serp import TalordataSerpToolSpec


async def main() -> None:
    tool_spec = TalordataSerpToolSpec(api_key="sk_xxx")

    agent = FunctionAgent(
        tools=tool_spec.to_tool_list(),
        llm=OpenAI(model="gpt-4.1"),
    )

    response = await agent.run("Find three recent search results for coffee market trends.")
    print(response)


asyncio.run(main())
```

## Tools

### `search_engine`

Search Google, Bing, Yandex, or DuckDuckGo and return normalized web results.

```plaintext
result = tool_spec.search_engine(
    query="coffee",
    engine="google",
    country="us",
    language="en",
    num=3,
)
```

### `image_search`

Search Bing Images or Google Images and return normalized image results.

```plaintext
result = tool_spec.image_search(
    query="coffee",
    engine="bing_images",
    country="us",
    language="en",
    count=3,
)
```

### `news_search`

Search Google News or Bing News and return normalized news-style results.

```plaintext
result = tool_spec.news_search(
    query="markets",
    engine="google_news",
    country="us",
    language="en",
)
```

### `raw_serp_request`

Pass an engine and extra JSON parameters directly to the Talordata SERP API. Use this when you need engine-specific parameters that are not exposed by the normalized helpers.

```plaintext
result = tool_spec.raw_serp_request(
    engine="google",
    query="coffee",
    params_json='{"num": 3, "country": "us", "language": "en"}',
)
```

## Response Shape

Normal search tools return a JSON string with this shape:

```plaintext
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

Agent-friendly errors are returned as JSON strings:

```plaintext
{
  "error": {
    "type": "SerpApiError",
    "status_code": 401,
    "message": "API key authentication failed"
  }
}
```

Set `include_raw=True` on normal tools when the caller needs the full upstream payload.

## Resources

*   PyPI: [LlamaIndex-talordata](https://pypi.org/project/llama-index-tools-talordata-serp/0.1.3/)
    
*   TalorData: [talordata.com](https://www.talordata.com/serp-api/llamaindex?campaignid=iiJFnZLYEox652MG&utm_source=LlamaIndex&utm_term=LlamaIndex)
    

## Support

For issues with the LlamaIndex integration package, report an issue in the [GitHub repository](https://github.com/talordata).

For TalorData SERP API account, quota, or API key issues, contact TalorData support through the support channel listed in your TalorData account or dashboard.

For detailed integration tutorials and API documentation, visit the TalorData Documentation.

---

## Learn More

Ready to build AI agents with real-time search in LlamaIndex?

**Explore the** [**TalorData LlamaIndex Integration Guide**](https://www.talordata.com/serp-api/llamaindex?campaignid=iiJFnZLYEox652MG&utm_source=LlamaIndex&utm_term=LlamaIndex)

**Read the** [**Integration Documentation**](https://docs.talordata.com/serp-api/integration/sdk-integration/how-to-integrate-talordata-with-llamaindex)

---
> **TalorData brings real-time search to LlamaIndex, enabling developers to build AI agents and workflows with fresh, structured, and reliable search data.**