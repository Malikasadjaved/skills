# Meta WhatsApp Cloud API — Error Codes Cheatsheet

Every error from the Graph API has a `code` (integer), `error_subcode` (integer),
and `message` (human-readable string). This reference explains what each code
means in plain English and what you should do about it.

---

## Permission & Authentication (codes 0–200)

| Code | Plain-English Meaning | Fix |
|---|---|---|
| `0` | Unknown / unclassified. The `message` field is your only clue. | Read the message carefully. Usually a malformed request body. |
| `1` | Rate-limited by Meta's global throttle. | Back off for a few seconds and retry. |
| `2` | Temporary server issue on Meta's side. | Retry with exponential backoff. |
| `4` | You hit the app-level rate limit. | Reduce request rate. Check the `X-Business-Use-Case-Usage` header. |
| `100` | A required parameter is missing or invalid. | Check every field in your JSON payload against the API reference. Common: missing `messaging_product`, wrong `type`, missing `to`. |
| `190` | Access token is expired, revoked, or invalid. | Generate a new token from the Meta Business app. System user tokens expire; rotate them. |
| `200` | Permission denied — your app lacks the required scope. | Check your app's permissions in the App Dashboard. |

---

## WhatsApp Business API (codes 130000+)

### Onboarding & Phone Numbers

| Code | Plain-English Meaning | Fix |
|---|---|---|
| `131000` | Something is wrong with the request but Meta won't say what. | Validate every field against the docs. Enable debug mode on your app. |
| `131001` | Message can't be empty. | You sent a `text` type with an empty body, or an interactive message with no action. |
| `131002` | Recipient phone number is invalid or not on WhatsApp. | Verify the number is real and registered on WhatsApp. Remember: no `+` prefix. |
| `131005` | Recipient can't receive this message type. | The user's WhatsApp version may not support interactive messages or the media type. |
| `131008` | Required parameter missing in your payload. | Check your JSON against the exact schema for the message type you're sending. |
| `131009` | Parameter value is invalid (wrong format, out of range). | Check field lengths, enum values, and data types. |
| `131015` | This account has been flagged or restricted. | Check Business Manager > Account Quality. You may need to appeal. |
| `131016` | Phone number not connected to a WhatsApp Business Account. | Register the number in Meta Business Manager under WhatsApp Accounts. |
| `131021` | Certificate or webhook endpoint is misconfigured. | Verify your webhook URL is HTTPS and returns the challenge correctly. |
| `131026` | Message contains content blocked by Meta's policy. | Review the Commerce and Business policies. Remove URLs that look spammy. |

### Messaging Window & Opt-in

| Code | Plain-English Meaning | Fix |
|---|---|---|
| `131030` | Recipient hasn't opted in — you can't send freeform. | Send an approved template message first. Once they reply, the 24hr window opens. |
| `131047` | The 24-hour customer service window has closed. | Switch to template messages only. Or ask the user to send you a message again. |
| `131048` | Sending freeform to a user who blocked you or deleted the chat. | Don't retry. Remove them from your outreach list. |
| `131049` | You're outside the 24hr window AND you don't have an approved template. | Get templates approved in the WhatsApp Manager, or wait for the user to message you. |
| `131051` | You reached the free-entry-point conversation limit. | WhatsApp allows only a certain number of business-initiated conversations per user. Wait for the user to message first. |
| `131052` | Recipient is on an older WhatsApp version that doesn't support this feature. | Fall back to plain text or a simpler message type. |
| `131053` | Recipient's phone can't display this message (e.g., very old phone). | Fall back to text-only. |

### Templates (HSM)

| Code | Plain-English Meaning | Fix |
|---|---|---|
| `132000` | Template name doesn't exist. | Check the template name exactly — it's case-sensitive. Must match the name in WhatsApp Manager. |
| `132001` | Template has a different language than what you specified. | Match the `language.code` in your request to an approved translation of the template. |
| `132005` | Template component parameter count mismatch. | You sent 3 params but the template expects 2. Count your header, body, and button params. |
| `132007` | Template parameter value is too long. | Shorten the dynamic text. Check WhatsApp Manager for per-parameter character limits. |
| `132008` | Template is paused, rejected, or disabled. | Go to WhatsApp Manager > Message Templates. Re-enable or re-submit. |
| `132012` | Template doesn't have a version in this language. | Same as 132001 — the language code doesn't match any approved translation. |
| `132016` | Template category mismatch. You're sending a marketing template where only utility is allowed (or vice versa). | Check the template category. Marketing templates have tighter restrictions. |
| `132068` | Template quality is low or it got flagged by Meta's review. | Review the template content. Check for policy violations, broken variable placeholders, or low engagement. |
| `136012` | Template not found in the specified language. | Most common with `en` vs `en_US`. Use the exact language code from WhatsApp Manager. |

### Media

| Code | Plain-English Meaning | Fix |
|---|---|---|
| `133000` | Media upload failed — file type not supported. | Check supported formats: jpg, jpeg, png for images; mp4, 3gpp for video; pdf, docx for documents. |
| `133001` | Media file is too large. | Images: 5 MB max. Video: 16 MB max. Documents: 100 MB max. Compress before uploading. |
| `133002` | Media download from your URL failed. | Make sure the URL is publicly accessible. Meta's servers must be able to GET it. |
| `133003` | Media download timed out. | The URL is too slow. Host the file on a CDN or reduce the file size. |
| `133004` | Media ID is invalid or expired. | Media IDs expire after 30 days. Re-upload if needed. |
| `133010` | You can't use this media ID — it belongs to a different WABA. | Media IDs are scoped to a WhatsApp Business Account. Upload again under the correct WABA. |

### Rate Limits

| Code | Plain-English Meaning | Fix |
|---|---|---|
| `130429` | Rate limit hit. You're sending too fast. | Default limits: 80 messages/sec for text, 500 business-initiated conversations/day for marketing. Back off and retry. |
| `134004` | Too many requests to a single phone number in a short period. | Don't send more than a few messages per minute to the same recipient. WhatsApp flags this as spam. |
| `134009` | You've hit the free-tier limit for this billing period. | Upgrade your plan or wait for the next billing cycle. |
| `134010` | You've exhausted your monthly messaging budget. | Increase budget in Business Manager or wait for the reset. |

### Webhooks

| Code | Plain-English Meaning | Fix |
|---|---|---|
| `135000` | Webhook URL not reachable. | Meta can't connect to your server. Check that it's HTTPS, the cert is valid, and it's not behind a firewall. |
| `135001` | Webhook verification failed — wrong verify token. | Make sure `hub.verify_token` in your GET handler matches what you entered in WhatsApp Manager. |
| `135002` | Webhook returned a non-200 status during verification. | Your GET /webhook handler must return exactly the `hub.challenge` value with a 200 status. |
| `135003` | Webhook delivery is failing at a high rate. | Check your POST /webhook handler. If it's slow or error-prone, Meta may throttle or disable delivery. |

### Business & Billing

| Code | Plain-English Meaning | Fix |
|---|---|---|
| `136000` | WhatsApp Business Account (WABA) is not verified. | Complete Business Verification in Facebook Business Manager. |
| `136001` | WABA is restricted or banned. | Go to Business Manager > Account Quality. Check for policy violations and appeal if needed. |
| `136002` | Phone number is not associated with this WABA. | Register the phone number under the correct WhatsApp Business Account. |
| `136003` | Phone number certificate is missing or invalid. | Re-register the phone number. The certificate may have expired. |
| `136004` | Two-step verification is enabled on the number but code not provided. | Provide the two-step verification PIN when registering. |
| `136005` | You're trying to register a number already registered to another WABA. | Delete the number from the other WABA first, or use a different number. |
| `136025` | Message failed — this phone number was recently recycled (new owner). | The user's number changed owners. Wait for re-opt-in or remove from your list. |

### Conversation Pricing & Spam

| Code | Plain-English Meaning | Fix |
|---|---|---|
| `137000` | Too many messages sent to users who haven't responded. | WhatsApp tracks engagement. If your open rate is very low, they throttle you. Clean your recipient list. |
| `137001` | Your message template has a high block/report rate. | Pause that template and revise the content. Users are reporting it as spam. |
| `137002` | Your phone number quality rating has dropped. | Check WhatsApp Manager > Phone Numbers > Quality Rating. If it's "Low" or "Flagged", improve message quality. |

---

## HTTP Status Codes

| HTTP Status | Meaning | Action |
|---|---|---|
| `200` | Success. | The message was accepted. Note: accepted ≠ delivered. Check webhook for delivery status. |
| `400` | Bad request — your JSON is wrong. | Validate payload structure, field names, and types. |
| `401` | Unauthorized — token missing or invalid. | Check `Authorization: Bearer <token>` header. Refresh expired tokens. |
| `403` | Forbidden — app lacks permissions or number not connected. | Check app permissions and WABA configuration. |
| `404` | Endpoint or resource not found. | Check the API version and phone number ID. |
| `429` | Too many requests. | Back off and retry. See `X-Business-Use-Case-Usage` header for limits. |
| `500` | Meta internal server error. | Retry with exponential backoff. If it persists, check the Meta status page. |

---

## Retry Strategy by Error Category

```
Client error (4xx, codes 100, 131030, 131047, 132008, 136012):
  → Do NOT retry. Fix the request or user state first.

Server error (5xx, codes 2):
  → Retry up to 3× with exponential backoff: 2s, 4s, 8s.

Rate limit (429, codes 1, 4, 130429, 134004):
  → Retry with jittered exponential backoff: 4s ± random, 16s ± random, 64s ± random.

Permission/auth (codes 190, 200):
  → Do NOT retry. Refresh the token or fix app permissions.
```

## Quick Debug Checklist

1. Read the **full** `error.error_data.details` if present — it often has the exact field that failed.
2. Check `messaging_product` is set to `"whatsapp"` — the #1 cause of cryptic 400s.
3. Check `to` has no `+` prefix — `923001234567`, not `+923001234567`.
4. Verify the `type` field matches your payload structure (text→`text`, template→`template`, image→`image`).
5. For templates: confirm the exact language code (`en`, `en_US`, `en_GB`) matches an approved translation.
6. For media: the file must be publicly accessible. Private S3 URLs will fail with 133002.
