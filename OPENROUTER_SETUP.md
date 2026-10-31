# ASPIRLY OpenRouter Setup

Render environment variables:
- DATABASE_URL = your existing PostgreSQL connection string
- SECRET_KEY = your existing Flask secret
- OPENROUTER_API_KEY = your OpenRouter API key
- ASPIRLYAI_MODEL = openrouter/free   (optional; this is already the code default)

ASPIRLY keeps its live public-web retrieval using DuckDuckGo and sends the retrieved evidence plus the student's profile to OpenRouter for synthesis.

The default `openrouter/free` router selects an available free model. Free model availability and rate limits can change on OpenRouter.

Do NOT set HF_TOKEN for this version. No OpenAI, Gemini, or Anthropic key is required.
