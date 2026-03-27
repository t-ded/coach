---
name: add-provider
description: Step-by-step guide for adding a new LLM provider to the coach app. Use this skill when the user asks to add support for a new AI provider or LLM.
---

Add a new LLM provider to the coach app.

Steps:
1. Implement `LLMClient` ABC in `coach/reasoning/clients.py` — add a new class that wraps the provider SDK
2. In `coach/reasoning/providers.py`:
   - Add the provider name to `_ENV_KEYS` dict (maps provider name → env var name)
   - Add a case in `create_llm_client()` to instantiate the new client
   - Add a case in `resolve_provider_and_key()` to resolve the key (from Vault or env)
3. Add the provider name to the valid providers list in the UI flow (`coach/web/profile_flow.py` or `coach/web/coaching.py` — wherever provider selection is handled)
4. Update tests in `coach/reasoning/tests/` to cover the new provider
5. Document the new provider's env var in CLAUDE.md and README if it's an operator-supplied key

Key constraint: API keys are stored in Supabase Vault via `upsert_api_key` / `get_api_key` RPC functions (same pattern as Strava tokens). The raw key must never enter the Chainlit chat stream — entry goes through the FastAPI form at `/oauth/api-key`.
