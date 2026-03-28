# Roadmap

Phases 1–5 are complete. The app is live at https://coach-production-e0b4.up.railway.app/.

## Phase 6 — Chat persistence (implemented on `feat/chat-session-persistence`)
- [x] `sessions` + `messages` tables in Supabase with RLS (#60 — user runs SQL)
- [x] Domain models + repositories with cap enforcement (#61)
- [x] Auto-save sessions + auto-title from first message (#62)
- [x] Chat Sessions panel with Threads/Recent list view (#63)
- [x] Session re-entry with full message history display (#64)
- [x] Lazy LLM summary + coach context injection on re-entry (#65)
- [x] Session management: rename, delete, promote (#66)

### Phase 6 v2 (deferred)
- Mid-session thread switching without page reload (currently renders in-chat)
- Activity delta surfacing ("new since last session")
- Session search/filtering

## Deferred items (from earlier phases)
- Enable `pg_cron` in Supabase for periodic cleanup of expired `strava_oauth_state` rows
- Activity feed / history view in the UI
