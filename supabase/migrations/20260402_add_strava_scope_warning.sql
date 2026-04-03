-- Add strava_scope_warning flag to users table.
-- Set to TRUE in the OAuth callback when the athlete did not grant activity:read_all.
-- Checked and cleared at the start of the next chat session.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS strava_scope_warning BOOLEAN NOT NULL DEFAULT FALSE;
