# Strava Webhook Setup

Strava webhooks deliver activity and deauthorization events in real time, replacing per-session polling. This is a **one-time operator action** that must be performed after the first deployment (and repeated if the callback URL changes).

## Prerequisites

- The app is deployed and reachable at a stable public URL (e.g. `https://coach-production-e0b4.up.railway.app`)
- `STRAVA_WEBHOOK_VERIFY_TOKEN` is set in the Railway environment (pick any random string — treat it like a password)
- You have your Strava app's `client_id` and `client_secret` (from [strava.com/settings/api](https://www.strava.com/settings/api))

## Register the subscription

Run the following `curl` command once. Replace the placeholders with your actual values.

```bash
curl -X POST https://www.strava.com/api/v3/push_subscriptions \
  -F client_id=YOUR_STRAVA_CLIENT_ID \
  -F client_secret=YOUR_STRAVA_CLIENT_SECRET \
  -F callback_url=https://YOUR_RAILWAY_URL/oauth/webhook/strava \
  -F verify_token=YOUR_STRAVA_WEBHOOK_VERIFY_TOKEN
```

Strava will immediately send a GET request to `callback_url` with a challenge. The app validates `verify_token` and echoes the challenge back. If everything is configured correctly, Strava responds with a subscription ID:

```json
{"id": 12345}
```

Save the subscription ID — you may need it to delete or inspect the subscription later.

## Verify the subscription

```bash
curl -G https://www.strava.com/api/v3/push_subscriptions \
  -d client_id=YOUR_STRAVA_CLIENT_ID \
  -d client_secret=YOUR_STRAVA_CLIENT_SECRET
```

## Delete the subscription (if re-registering)

If the callback URL changes (e.g. a new Railway deployment domain), delete the old subscription first:

```bash
curl -X DELETE "https://www.strava.com/api/v3/push_subscriptions/YOUR_SUBSCRIPTION_ID" \
  -F client_id=YOUR_STRAVA_CLIENT_ID \
  -F client_secret=YOUR_STRAVA_CLIENT_SECRET
```

Then re-register with the new URL.

## Setting STRAVA_WEBHOOK_VERIFY_TOKEN in Railway

In the Railway dashboard → your service → **Variables**, add:

```
STRAVA_WEBHOOK_VERIFY_TOKEN = <your chosen secret string>
```

The app will refuse to start the webhook challenge response if this variable is missing.

## Event types handled

| `object_type` | `aspect_type`     | Action                                               |
|---------------|-------------------|------------------------------------------------------|
| `athlete`     | `deauthorization` | Delete tokens, activities, and clear strava_user_id  |
| `activity`    | `create`          | Fetch full detail from Strava API and upsert         |
| `activity`    | `update`          | Fetch full detail from Strava API and upsert         |
| `activity`    | `delete`          | Delete activity from database                        |

All other event types are ignored and return HTTP 200.

## Notes

- Strava allows only one active webhook subscription per application.
- Strava retries failed deliveries. The endpoint returns HTTP 200 immediately after basic validation to avoid triggering retries.
- The webhook endpoint is mounted at `/oauth/webhook/strava` in the FastAPI sub-app.
