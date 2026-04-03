-- RPC to delete a user's Strava tokens from Vault.
-- Called by the deauthorization service when an athlete disconnects the app from Strava.
-- Mirrors the existing upsert_strava_tokens RPC — adapt the body to match your vault schema
-- (replace strava_tokens table/column names if they differ).
CREATE OR REPLACE FUNCTION delete_strava_tokens(p_user_id UUID)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_secret_id UUID;
BEGIN
    -- Locate the vault secret ID associated with this user's Strava tokens
    SELECT secret_id INTO v_secret_id
    FROM private.strava_tokens
    WHERE user_id = p_user_id;

    IF v_secret_id IS NOT NULL THEN
        PERFORM vault.delete_secret(v_secret_id);
        DELETE FROM private.strava_tokens WHERE user_id = p_user_id;
    END IF;
END;
$$;
