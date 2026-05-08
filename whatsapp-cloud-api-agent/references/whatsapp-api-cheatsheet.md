# WhatsApp Cloud API — Quick Reference

## Base URL

```
https://graph.facebook.com/{version}/{phone_number_id}/messages
```

Current version: `v23.0` (update via `WHATSAPP_API_VERSION` env var).

## Authentication

```
Authorization: Bearer {WHATSAPP_TOKEN}
```

Token comes from Meta Business App → System User → Generate Token.
Tokens expire; set up a cron job to refresh via system user API.

---

## Send Message — Minimal Payload

```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "923001234567",
  "type": "text",
  "text": { "body": "Hello from Digital FTE" }
}
```

**Always include `"messaging_product": "whatsapp"`** — Meta uses it for internal routing.

---

## Message Types Overview

| Type | `"type"` value | Freeform? | Notes |
|------|---------------|-----------|-------|
| Text | `"text"` | Yes | Within 24hr window only |
| Template | `"template"` | No | Pre-approved, works outside 24hr window |
| Image | `"image"` | Yes | By `id` (uploaded) or `link` (URL) |
| Document | `"document"` | Yes | PDF, DOCX, XLSX — max 100MB by id, 64MB by link |
| Audio | `"audio"` | Yes | OGG, MP3, AAC — max 16MB |
| Video | `"video"` | Yes | MP4, 3GPP — max 16MB |
| Interactive (button) | `"interactive"` | Yes | Up to 3 buttons |
| Interactive (list) | `"interactive"` | Yes | Up to 10 rows in sections |
| Location | `"location"` | Yes | lat/long + name + address |
| Contacts | `"contacts"` | Yes | vCard format |
| Reaction | `"reaction"` | Yes | Emoji reaction to a prior message |
| Sticker | `"sticker"` | Yes | By id or link |

---

## Send Text

```json
{
  "messaging_product": "whatsapp",
  "to": "923001234567",
  "type": "text",
  "text": { "preview_url": true, "body": "Check out https://digitalfte.com" }
}
```

---

## Send Template (HSM)

```json
{
  "messaging_product": "whatsapp",
  "to": "923001234567",
  "type": "template",
  "template": {
    "name": "hello_world",
    "language": { "code": "en" }
  }
}
```

With parameters:

```json
{
  "messaging_product": "whatsapp",
  "to": "923001234567",
  "type": "template",
  "template": {
    "name": "appointment_reminder",
    "language": { "code": "en" },
    "components": [
      {
        "type": "header",
        "parameters": [{ "type": "text", "text": "Al-Shifa Clinic" }]
      },
      {
        "type": "body",
        "parameters": [
          { "type": "text", "text": "Ahmed Khan" },
          { "type": "text", "text": "15 May 2026" },
          { "type": "text", "text": "10:00 AM" }
        ]
      },
      {
        "type": "button",
        "sub_type": "quick_reply",
        "index": "0",
        "parameters": [{ "type": "text", "text": "15 May 2026" }]
      }
    ]
  }
}
```

---

## Send Interactive Buttons (up to 3)

```json
{
  "messaging_product": "whatsapp",
  "to": "923001234567",
  "type": "interactive",
  "interactive": {
    "type": "button",
    "header": { "type": "text", "text": "Confirm Appointment" },
    "body": { "text": "Your appointment is on 15 May at 10 AM. Confirm?" },
    "footer": { "text": "Al-Shifa Clinic" },
    "action": {
      "buttons": [
        { "type": "reply", "reply": { "id": "confirm_yes", "title": "Yes" } },
        { "type": "reply", "reply": { "id": "confirm_no", "title": "No" } },
        { "type": "reply", "reply": { "id": "confirm_reschedule", "title": "Reschedule" } }
      ]
    }
  }
}
```

---

## Send Interactive List (up to 10 rows)

```json
{
  "messaging_product": "whatsapp",
  "to": "923001234567",
  "type": "interactive",
  "interactive": {
    "type": "list",
    "header": { "type": "text", "text": "Our Services" },
    "body": { "text": "What do you need help with?" },
    "footer": { "text": "Reply with a number" },
    "action": {
      "button": "Choose",
      "sections": [
        {
          "title": "Accounting",
          "rows": [
            { "id": "svc_invoice", "title": "Create Invoice", "description": "Generate a new invoice" },
            { "id": "svc_pl", "title": "P&L Report", "description": "Profit & loss statement" },
            { "id": "svc_bs", "title": "Balance Sheet", "description": "Current balance sheet" }
          ]
        },
        {
          "title": "HR",
          "rows": [
            { "id": "svc_leave", "title": "Leave Request", "description": "Apply for time off" },
            { "id": "svc_payslip", "title": "Payslip", "description": "View current payslip" }
          ]
        }
      ]
    }
  }
}
```

---

## Send Image

By media_id (after upload):
```json
{
  "messaging_product": "whatsapp",
  "to": "923001234567",
  "type": "image",
  "image": { "id": "123456789", "caption": "Your lab report" }
}
```

By URL:
```json
{
  "messaging_product": "whatsapp",
  "to": "923001234567",
  "type": "image",
  "image": { "link": "https://example.com/report.png", "caption": "Your lab report" }
}
```

---

## Send Document

```json
{
  "messaging_product": "whatsapp",
  "to": "923001234567",
  "type": "document",
  "document": { "id": "123456789", "filename": "invoice-0042.pdf", "caption": "Invoice #0042" }
}
```

---

## Upload Media (get media_id)

```
POST https://graph.facebook.com/{version}/{phone_number_id}/media
Content-Type: multipart/form-data

Fields:
  file: (binary)
  type: image/png (or application/pdf, audio/ogg, etc.)
  messaging_product: whatsapp
```

Response: `{ "id": "123456789" }`

---

## Mark Message as Read

```json
{
  "messaging_product": "whatsapp",
  "status": "read",
  "message_id": "wamid.xxxxx"
}
```

POST to the same `/messages` endpoint. Shows blue double-tick on sender's phone.

---

## Webhook Verification (GET)

```
GET /webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=123456
→ 200 with body: 123456
```

Meta sends this when you configure the webhook URL. Your server must:
1. Verify `hub.mode` == `subscribe`
2. Verify `hub.verify_token` matches your configured token
3. Return `hub.challenge` as a plain integer

---

## Webhook POST Payload Shape

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "923001234567",
          "phone_number_id": "PHONE_NUMBER_ID"
        },
        "messages": [{
          "from": "923001234567",
          "id": "wamid.xxxxx",
          "timestamp": "1715630400",
          "type": "text",
          "text": { "body": "Hello" }
        }]
      },
      "field": "messages"
    }]
  }]
}
```

### Status-only webhook (no messages[]):

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WABA_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": { "display_phone_number": "...", "phone_number_id": "..." },
        "statuses": [{
          "id": "wamid.xxxxx",
          "status": "delivered",
          "timestamp": "1715630401",
          "recipient_id": "923001234567"
        }]
      },
      "field": "messages"
    }]
  }]
}
```

Status values: `sent`, `delivered`, `read`, `failed`, `deleted`.

---

## Interactive Reply Payloads

When a user taps a button:
```json
{
  "type": "interactive",
  "interactive": {
    "type": "button_reply",
    "button_reply": { "id": "confirm_yes", "title": "Yes" }
  }
}
```

When a user selects from a list:
```json
{
  "type": "interactive",
  "interactive": {
    "type": "list_reply",
    "list_reply": { "id": "svc_invoice", "title": "Create Invoice", "description": "Generate a new invoice" }
  }
}
```

---

## Error Codes

| HTTP | Code | Meaning | Retry? |
|------|------|---------|--------|
| 400 | 100 | Invalid parameter | No — fix payload |
| 400 | 131008 | Required parameter missing | No |
| 400 | 131030 | Recipient not in allowed list | No — need opt-in |
| 400 | 131047 | Re-engagement window expired | No — switch to template |
| 400 | 131051 | Template not found | No — check name |
| 400 | 136012 | Template not in requested language | No |
| 400 | 136015 | Template component count mismatch | No |
| 401 | 190 | Invalid/expired access token | No — refresh token |
| 429 | 130429 | Rate limit | Yes — exponential backoff |
| 429 | 131000 | Too many messages | Yes |
| 429 | 131001 | Too many template messages | Yes |
| 429 | 131005 | Too many marketing messages | Yes |
| 500 | 1 | Temporary server error | Yes |

### Rate limits (defaults):
- Text/media/freeform: 80 messages/second
- Marketing templates: 500 unique recipients/day (unverified), 1,000 (verified)
- Utility templates: 10,000 messages/day (unverified), unlimited (verified)
- Authentication templates: 1,000 messages/day

---

## Media ID Retrieval (download incoming media)

```
GET https://graph.facebook.com/{version}/{media_id}
Header: Authorization: Bearer {WHATSAPP_TOKEN}

Response: { "id": "...", "url": "https://..." }
```

Use the `url` field to download the file — it expires after 5 minutes.

---

## Business Phone Number Info

```
GET https://graph.facebook.com/{version}/{phone_number_id}
Header: Authorization: Bearer {WHATSAPP_TOKEN}

Response: {
  "id": "...",
  "display_phone_number": "923001234567",
  "verified_name": "Digital FTE",
  "code_verification_status": "VERIFIED",
  "quality_rating": "GREEN",
  "status": "CONNECTED"
}
```

---

## Phone Number IDs vs WABA IDs

- **Phone Number ID** (`WHATSAPP_PHONE_NUMBER_ID`): Used in `/messages` URL. One per phone number.
- **WABA ID** (`WHATSAPP_BUSINESS_ACCOUNT_ID`): The business account owning the phone number. Found in webhook `entry[0].id`.
- **App ID**: The Meta app that owns the WABA. Not used in API calls directly.

---

## Signature Verification (X-Hub-Signature-256)

```
Header: X-Hub-Signature-256: sha256=<hex-digest>
Body: raw bytes of the request body
Key: META_APP_SECRET (from Meta App Dashboard → Settings → Basic)
Algorithm: HMAC-SHA256
```

```python
import hmac, hashlib
expected = signature_header.removeprefix("sha256=")
computed = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
valid = hmac.compare_digest(expected, computed)
```

Always use `hmac.compare_digest()` — never `==` for signature comparison.

---

## Common Pitfalls Summary

1. **Missing `messaging_product`** → cryptic 400 error
2. **Phone number includes `+`** → WhatsApp IDs never have `+`
3. **Freeform outside 24hr window** → error 131047
4. **No signature verification** → anyone can POST to your webhook
5. **Slow 200 response** → Meta retries, duplicate processing
6. **Ignoring status-only webhooks** → parser crashes on `statuses`
7. **Template params not matching Meta's count** → error 136015
8. **Storing media URLs indefinitely** → they expire in 5 minutes
9. **Using wrong `Content-Type`** → must be `application/json` for messages
10. **Not calling mark-as-read** → user doesn't see blue ticks
