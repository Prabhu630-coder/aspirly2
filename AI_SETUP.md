# AspirlyAI 3.1 — HF-powered real research agent

AspirlyAI uses a real reasoning model through the OpenRouter Inference Providers API. The model plans research queries, public web pages are retrieved, and the model analyzes the evidence before answering. It does not use the old canned TF-IDF answer engine.

## Required on Render

Set only:

- `OPENROUTER_API_KEY` — OpenRouter User Access Token with permission to make inference calls.

Optional:

- `ASPIRLYAI_MODEL` — defaults to `openrouter/free`. If that model/provider is unavailable, AspirlyAI automatically retries with `openrouter/free`, using the same HF token.

No Tavily key, OpenAI key, or other AI API key is required. Public web retrieval uses DuckDuckGo HTML as the no-key research source; OpenRouter performs the planning and final reasoning.

If the HF request fails, the server logs the real exception instead of silently returning a fake answer.
