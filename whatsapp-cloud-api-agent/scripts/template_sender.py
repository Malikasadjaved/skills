"""
WhatsApp Cloud API — Template Message Sender.

Sends approved HSM (Highly Structured Message) templates via the Graph API.
Templates are pre-approved by Meta and are the only way to message users
outside the 24-hour customer service window.

Includes retry with exponential backoff for rate limits (130429) and
graceful handling of re-engagement window errors (131047).

Usage:
    python scripts/template_sender.py --to 923001234567 --template appointment_reminder \\
        --lang en --params '{"name":"Ahmed","clinic":"Al-Shifa","date":"15 May 2026"}'

    python scripts/template_sender.py --to 923001234567 --template payment_confirmation \\
        --lang ur --params '{"amount":"Rs. 5,000","ref":"INV-2026-0042"}'
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("whatsapp.templates")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v23.0")
WHATSAPP_API_URL = "https://graph.facebook.com"

BASE_URL = f"{WHATSAPP_API_URL}/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

# Retryable error codes
RATE_LIMIT_CODES = {130429, 131000, 131001, 131005, 131006}
NON_RETRYABLE_CODES = {131030, 131047, 136012, 100, 190}


class TemplateSendError(Exception):
    def __init__(self, code: int, message: str, detail: dict | None = None):
        self.code = code
        self.message = message
        self.detail = detail or {}
        super().__init__(f"[{code}] {message}")


def _text_param(value: str) -> dict:
    return {"type": "text", "text": value}


async def send_template(
    to: str,
    template_name: str,
    language_code: str = "en",
    header_params: list[str] | None = None,
    body_params: list[str] | None = None,
    button_params: list[str] | None = None,
    max_retries: int = 3,
) -> dict:
    """Send an approved template message with retry logic."""
    components = []

    if header_params:
        components.append({
            "type": "header",
            "parameters": [_text_param(v) for v in header_params],
        })
    if body_params:
        components.append({
            "type": "body",
            "parameters": [_text_param(v) for v in body_params],
        })
    if button_params:
        components.append({
            "type": "button",
            "sub_type": "quick_reply",
            "index": "0",
            "parameters": [_text_param(v) for v in button_params],
        })

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }

    if components:
        payload["template"]["components"] = components

    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    last_error = None
    for attempt in range(max_retries):
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(BASE_URL, json=payload, headers=headers)

            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Template sent: {template_name} → {to}")
                return data

            data = resp.json()
            err = data.get("error", {})
            code = err.get("code", resp.status_code)
            msg = err.get("message", resp.text)

            if code in NON_RETRYABLE_CODES:
                raise TemplateSendError(code, msg, err.get("error_data", {}))

            if code in RATE_LIMIT_CODES or resp.status_code == 429:
                wait = 2 ** attempt
                logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries}), waiting {wait}s...")
                await asyncio.sleep(wait)
                last_error = TemplateSendError(code, msg, err.get("error_data", {}))
                continue

            raise TemplateSendError(code, msg, err.get("error_data", {}))

    raise last_error or TemplateSendError(-1, f"Exhausted {max_retries} retries")


# --- Pre-built templates for clinic/business use cases ---

class ClinicTemplates:
    """Pre-configured templates for a Pakistani clinic use case."""

    @staticmethod
    async def appointment_reminder(to: str, patient_name: str, clinic_name: str, date: str, time: str) -> dict:
        return await send_template(
            to=to,
            template_name="appointment_reminder",
            language_code="en",
            header_params=[clinic_name],
            body_params=[patient_name, date, time],
            button_params=[f"{date} {time}"],
        )

    @staticmethod
    async def appointment_confirmation(to: str, patient_name: str, doctor_name: str, date: str, time: str) -> dict:
        return await send_template(
            to=to,
            template_name="appointment_confirmation",
            language_code="en",
            header_params=[doctor_name],
            body_params=[patient_name, date, time],
        )

    @staticmethod
    async def payment_receipt(to: str, patient_name: str, amount: str, ref_number: str) -> dict:
        return await send_template(
            to=to,
            template_name="payment_receipt",
            language_code="en",
            body_params=[patient_name, amount, ref_number],
        )

    @staticmethod
    async def lab_results_ready(to: str, patient_name: str, test_name: str) -> dict:
        return await send_template(
            to=to,
            template_name="lab_results_ready",
            language_code="en",
            header_params=["Lab Results"],
            body_params=[patient_name, test_name],
        )


class BusinessTemplates:
    """Pre-configured templates for general business use cases."""

    @staticmethod
    async def invoice_ready(to: str, client_name: str, invoice_number: str, amount: str, due_date: str) -> dict:
        return await send_template(
            to=to,
            template_name="invoice_ready",
            language_code="en",
            header_params=["Invoice Ready"],
            body_params=[client_name, invoice_number, amount, due_date],
        )

    @staticmethod
    async def payment_confirmation(to: str, client_name: str, amount: str, ref_number: str) -> dict:
        return await send_template(
            to=to,
            template_name="payment_confirmation",
            language_code="en",
            body_params=[client_name, amount, ref_number],
        )

    @staticmethod
    async def meeting_reminder(to: str, attendee_name: str, meeting_title: str, date: str, time: str) -> dict:
        return await send_template(
            to=to,
            template_name="meeting_reminder",
            language_code="en",
            header_params=[meeting_title],
            body_params=[attendee_name, date, time],
            button_params=[f"{date} {time}"],
        )


# --- Batch sender ---

async def send_batch(recipients: list[dict], template_name: str, language_code: str = "en", delay: float = 0.5):
    """Send a template to multiple recipients with configurable delay.

    recipients is a list of dicts with 'to', 'header_params', 'body_params', 'button_params'.
    """
    results = []
    for i, recipient in enumerate(recipients):
        try:
            result = await send_template(
                to=recipient["to"],
                template_name=template_name,
                language_code=language_code,
                header_params=recipient.get("header_params"),
                body_params=recipient.get("body_params"),
                button_params=recipient.get("button_params"),
            )
            results.append({"to": recipient["to"], "status": "sent", "wa_id": result.get("messages", [{}])[0].get("id")})
        except TemplateSendError as e:
            logger.error(f"Failed for {recipient['to']}: [{e.code}] {e.message}")
            results.append({"to": recipient["to"], "status": "failed", "error": e.message})
        except Exception as e:
            logger.error(f"Unexpected error for {recipient['to']}: {e}")
            results.append({"to": recipient["to"], "status": "failed", "error": str(e)})

        if i < len(recipients) - 1:
            await asyncio.sleep(delay)

    return results


# --- CLI ---

async def _main():
    parser = argparse.ArgumentParser(description="Send WhatsApp template messages")
    parser.add_argument("--to", required=True, help="Recipient phone number (no +)")
    parser.add_argument("--template", required=True, help="Approved template name")
    parser.add_argument("--lang", default="en", help="Language code (default: en)")
    parser.add_argument("--params", default="{}", help="JSON string of template parameters")
    parser.add_argument("--header", help="Comma-separated header params")
    parser.add_argument("--body", help="Comma-separated body params")
    parser.add_argument("--buttons", help="Comma-separated button params")
    parser.add_argument("--batch", help="Path to JSON file with batch recipients")

    args = parser.parse_args()

    if not WHATSAPP_TOKEN:
        print("Error: WHATSAPP_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)
    if not WHATSAPP_PHONE_NUMBER_ID:
        print("Error: WHATSAPP_PHONE_NUMBER_ID not set in .env", file=sys.stderr)
        sys.exit(1)

    if args.batch:
        with open(args.batch) as f:
            recipients = json.load(f)
        results = await send_batch(recipients, args.template, args.lang)
        print(json.dumps(results, indent=2))
        return

    # Parse params from CLI args or --params JSON
    if args.header or args.body or args.buttons:
        header_params = args.header.split(",") if args.header else None
        body_params = args.body.split(",") if args.body else None
        button_params = args.buttons.split(",") if args.buttons else None
    else:
        params = json.loads(args.params)
        header_params = None
        body_params = list(params.values()) if params else None
        button_params = None

    try:
        result = await send_template(
            to=args.to,
            template_name=args.template,
            language_code=args.lang,
            header_params=header_params,
            body_params=body_params,
            button_params=button_params,
        )
        print(json.dumps(result, indent=2))
    except TemplateSendError as e:
        print(f"API Error [{e.code}]: {e.message}", file=sys.stderr)
        if e.detail:
            print(f"  Detail: {json.dumps(e.detail)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(_main())
