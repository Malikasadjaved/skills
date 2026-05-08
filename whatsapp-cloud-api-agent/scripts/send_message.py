"""
WhatsApp Cloud API — Send text, template, interactive, and media messages.

Usage:
    python scripts/send_message.py text 923001234567 "Hello from Digital FTE"
    python scripts/send_message.py template 923001234567 appointment_reminder en '{"name":"Ahmed","clinic":"Al-Shifa","date":"15 May 2026"}'
    python scripts/send_message.py interactive 923001234567 routing_menu
    python scripts/send_message.py image 923001234567 /path/to/report.png
"""

import json
import sys
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v23.0")
WHATSAPP_API_URL = "https://graph.facebook.com"

BASE_URL = f"{WHATSAPP_API_URL}/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"


class WhatsAppAPIError(Exception):
    def __init__(self, code: int, message: str, detail: dict | None = None):
        self.code = code
        self.message = message
        self.detail = detail or {}
        super().__init__(f"[{code}] {message}")


async def _post(payload: dict) -> dict:
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(BASE_URL, json=payload, headers=headers)
        data = resp.json()
        if resp.status_code != 200:
            err = data.get("error", {})
            raise WhatsAppAPIError(
                code=err.get("code", resp.status_code),
                message=err.get("message", resp.text),
                detail=err.get("error_data", {}),
            )
        return data


async def send_text(to: str, body: str, preview_url: bool = False) -> dict:
    """Send a plain text message."""
    return await _post({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": preview_url, "body": body},
    })


async def send_template(
    to: str,
    template_name: str,
    language_code: str = "en",
    header_params: list[dict] | None = None,
    body_params: list[dict] | None = None,
    button_params: list[dict] | None = None,
) -> dict:
    """Send an approved HSM template message."""
    components = []
    if header_params:
        components.append({"type": "header", "parameters": header_params})
    if body_params:
        components.append({"type": "body", "parameters": body_params})
    if button_params:
        components.append({"type": "button", "sub_type": "quick_reply", "index": "0", "parameters": button_params})

    return await _post({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
            **({"components": components} if components else {}),
        },
    })


async def send_interactive_buttons(
    to: str,
    body: str,
    buttons: list[dict],
    header_text: str | None = None,
    footer_text: str | None = None,
) -> dict:
    """Send an interactive button message (up to 3 buttons)."""
    buttons_payload = [
        {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
        for b in buttons[:3]
    ]
    interactive: dict = {
        "type": "button",
        "body": {"text": body},
        "action": {"buttons": buttons_payload},
    }
    if header_text:
        interactive["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive["footer"] = {"type": "text", "text": footer_text}

    return await _post({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": interactive,
    })


async def send_interactive_list(
    to: str,
    body: str,
    button_label: str,
    sections: list[dict],
    header_text: str | None = None,
    footer_text: str | None = None,
) -> dict:
    """Send an interactive list message (up to 10 rows across sections)."""
    interactive: dict = {
        "type": "list",
        "body": {"text": body},
        "action": {"button": button_label, "sections": sections},
    }
    if header_text:
        interactive["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive["footer"] = {"type": "text", "text": footer_text}

    return await _post({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": interactive,
    })


async def send_image_by_id(to: str, media_id: str, caption: str | None = None) -> dict:
    """Send an image by pre-uploaded media_id."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "image",
        "image": {"id": media_id},
    }
    if caption:
        payload["image"]["caption"] = caption
    return await _post(payload)


async def send_image_by_url(to: str, image_url: str, caption: str | None = None) -> dict:
    """Send an image from a public URL."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "image",
        "image": {"link": image_url},
    }
    if caption:
        payload["image"]["caption"] = caption
    return await _post(payload)


async def send_document_by_id(to: str, media_id: str, filename: str, caption: str | None = None) -> dict:
    """Send a document by pre-uploaded media_id."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "document",
        "document": {"id": media_id, "filename": filename},
    }
    if caption:
        payload["document"]["caption"] = caption
    return await _post(payload)


async def send_document_by_url(to: str, doc_url: str, filename: str, caption: str | None = None) -> dict:
    """Send a document from a public URL."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "document",
        "document": {"link": doc_url, "filename": filename},
    }
    if caption:
        payload["document"]["caption"] = caption
    return await _post(payload)


async def send_audio_by_id(to: str, media_id: str) -> dict:
    """Send an audio message by pre-uploaded media_id."""
    return await _post({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "audio",
        "audio": {"id": media_id},
    })


async def upload_media(file_path: str, mime_type: str) -> str:
    """Upload media to WhatsApp and return the media_id."""
    media_url = f"{WHATSAPP_API_URL}/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    async with httpx.AsyncClient(timeout=60) as client:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, mime_type)}
            data = {"messaging_product": "whatsapp"}
            resp = await client.post(media_url, data=data, files=files, headers=headers)
            resp.raise_for_status()
            return resp.json()["id"]


ROUTING_MENU_BUTTONS = [
    {"id": "agent_finance", "title": "Finance"},
    {"id": "agent_legal", "title": "Legal"},
    {"id": "agent_hr", "title": "HR"},
]


# --- CLI ---

async def _main():
    if len(sys.argv) < 3:
        print("Usage: send_message.py <type> <to> [args...]")
        print("  text <to> <body>")
        print("  template <to> <name> <lang> <params_json>")
        print("  interactive <to> <menu_name>")
        print("  image <to> <file_path_or_url> [caption]")
        print("  document <to> <file_path_or_url> <filename> [caption]")
        sys.exit(1)

    msg_type = sys.argv[1]
    to = sys.argv[2]

    try:
        if msg_type == "text":
            body = sys.argv[3] if len(sys.argv) > 3 else ""
            result = await send_text(to, body)

        elif msg_type == "template":
            name = sys.argv[3]
            lang = sys.argv[4] if len(sys.argv) > 4 else "en"
            params = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}
            bp = [{"type": "text", "text": v} for v in params.values()]
            result = await send_template(to, name, lang, body_params=bp)

        elif msg_type == "interactive":
            menu = sys.argv[3] if len(sys.argv) > 3 else "routing_menu"
            if menu == "routing_menu":
                result = await send_interactive_buttons(
                    to,
                    "How can I help you today?",
                    ROUTING_MENU_BUTTONS,
                    header_text="Digital FTE Assistant",
                    footer_text="Powered by Digital FTE",
                )
            else:
                print(f"Unknown menu: {menu}")
                sys.exit(1)

        elif msg_type == "image":
            path_or_url = sys.argv[3]
            caption = sys.argv[4] if len(sys.argv) > 4 else None
            if path_or_url.startswith("http"):
                result = await send_image_by_url(to, path_or_url, caption)
            else:
                import mimetypes
                mime, _ = mimetypes.guess_type(path_or_url)
                media_id = await upload_media(path_or_url, mime or "image/png")
                result = await send_image_by_id(to, media_id, caption)

        elif msg_type == "document":
            path_or_url = sys.argv[3]
            filename = sys.argv[4] if len(sys.argv) > 4 else os.path.basename(path_or_url)
            caption = sys.argv[5] if len(sys.argv) > 5 else None
            if path_or_url.startswith("http"):
                result = await send_document_by_url(to, path_or_url, filename, caption)
            else:
                media_id = await upload_media(path_or_url, "application/pdf")
                result = await send_document_by_id(to, media_id, filename, caption)

        else:
            print(f"Unknown message type: {msg_type}")
            sys.exit(1)

        print(json.dumps(result, indent=2))

    except WhatsAppAPIError as e:
        print(f"API Error [{e.code}]: {e.message}", file=sys.stderr)
        if e.detail:
            print(f"  Detail: {json.dumps(e.detail)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(_main())
