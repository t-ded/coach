-- RPC to delete a user's Strava tokens from Vault.
-- Called by the deauthorization service when an athlete disconnects the app from Strava.
-- Schema: private.strava_tokens stores two vault secret IDs — one for the access token
-- and one for the refresh token — both of which must be deleted from the Vault.
CREATE OR REPLACE FUNCTION delete_strava_tokens(p_user_id UUID)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_access_token_vault_id UUID;
    v_refresh_token_vault_id UUID;
BEGIN
    SELECT access_token_vault_id, refresh_token_vault_id
    INTO v_access_token_vault_id, v_refresh_token_vault_id
    FROM private.strava_tokens
    WHERE user_id = p_user_id;

    IF v_access_token_vault_id IS NOT NULL THEN
        PERFORM vault.delete_secret(v_access_token_vault_id);
    END IF;

    IF v_refresh_token_vault_id IS NOT NULL THEN
        PERFORM vault.delete_secret(v_refresh_token_vault_id);
    END IF;

    DELETE FROM private.strava_tokens WHERE user_id = p_user_id;
END;
$$;
