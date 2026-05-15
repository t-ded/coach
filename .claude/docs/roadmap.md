# Roadmap

Phases 1–6 are complete. The app is live at https://coach-production-e0b4.up.railway.app/.

## Tier 1 — shipped

- [x] #103 — **Smart chat starters**: data-driven opening message at session start (replaces generic "Coach is ready")
- [x] #104 — **Anthropic (Claude) as provider**: user-keyed BYOK via the same flow as Google/OpenAI
- [x] #105 — **Post-activity email insights**: `NotificationService` + Resend; triggered by Strava webhook on activity create; 24h cooldown guard; `PushBackend` stub for future mobile

## Tier 2 — next (PRDs required before implementation)

- [ ] #106 — **Activity enrichment** (PRD): km splits + HR from Strava detailed API; pace zones derived from PBs; intensity breakdown in coach context
- [ ] #107 — **Prompt caching**: `cache_control` on static coaching context block (Anthropic); depends on #104
- [ ] #108 — **Freemium tier** (PRD): system Anthropic key + per-user usage caps + BYOK unlimited; depends on #104 + #107

## Roadmap — design later

- [ ] #109 — **Calendar integration** (PRD): workout planning collision detection; interactive (agent asks user) + automated (Google Calendar read) modes
- [ ] #110 — **Expanded activity types**: cycling + swimming enrichment; depends on #106

## Phase 6 — Chat persistence (complete)

- [x] `sessions` + `messages` tables with RLS
- [x] Domain models + repositories with cap enforcement
- [x] Auto-save sessions + auto-title from first message
- [x] Chat Sessions panel with Threads/Recent list view
- [x] Session re-entry with full message history display
- [x] Lazy LLM summary + coach context injection on re-entry
- [x] Session management: rename, delete, promote

### Phase 6 v2 (deferred)

- Mid-session thread switching without page reload
- Activity delta surfacing ("new since last session")
- Session search/filtering

## Deferred items

- Enable `pg_cron` in Supabase for periodic cleanup of expired `strava_oauth_state` rows
- Activity feed / history view in the UI
