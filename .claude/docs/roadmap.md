# Roadmap

Phases 1–5 are complete. The app is live at https://coach-production-e0b4.up.railway.app/.

## Phase 6 — Chat persistence
- [ ] Store chat threads and messages in Supabase (`threads` / `messages` tables with RLS)
- [ ] Load the most recent thread on chat start; restore `ChatHistory` from it
- [ ] Thread list / history view in the UI sidebar
- **Note:** API key entry goes through the FastAPI form route (`/oauth/api-key`) — the raw key never enters the Chainlit chat stream. When implementing chat persistence, confirm this route is not inadvertently captured in stored threads.

## Deferred items (from earlier phases)
- Enable `pg_cron` in Supabase for periodic cleanup of expired `strava_oauth_state` rows
- Activity feed / history view in the UI
