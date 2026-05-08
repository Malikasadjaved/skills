"""
Message Router — classify and dispatch WhatsApp messages to specialist agents.

Architecture:
    Webhook → classify_intent() → Agent dispatch (Kafka or direct)
              |
              └── Session-aware: if user is mid-conversation with an agent,
                   continue routing to that agent until RESOLVED.

Supports:
- Intent-based routing via keyword match
- Session-aware routing via Redis state
- Kafka publish for async agent dispatch (production)
- Direct agent call for simple deployments (development)

Usage as module:
    from scripts.message_router import MessageRouter, AgentDomain

    router = MessageRouter(settings, redis_client, kafka_producer=None)
    await router.route(message)
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger("whatsapp.router")


class AgentDomain(str, Enum):
    FINANCE = "finance"
    HR = "hr"
    LEGAL = "legal"
    SHARED = "shared"
    GENERAL = "general"


class ConvState(str, Enum):
    IDLE = "idle"
    GREETED = "greeted"
    COLLECTING_INFO = "collecting_info"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    RESOLVED = "resolved"


@dataclass
class Session:
    wa_id: str
    state: ConvState = ConvState.IDLE
    active_agent: str | None = None
    collected_data: dict = field(default_factory=dict)
    message_count: int = 0
    last_activity: float = 0.0

    def transition(self, new_state: ConvState):
        import time
        self.state = new_state
        self.last_activity = time.time()

    def to_dict(self) -> dict:
        return {
            "wa_id": self.wa_id,
            "state": self.state.value,
            "active_agent": self.active_agent,
            "collected_data": self.collected_data,
            "message_count": self.message_count,
            "last_activity": self.last_activity,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            wa_id=data["wa_id"],
            state=ConvState(data["state"]),
            active_agent=data.get("active_agent"),
            collected_data=data.get("collected_data", {}),
            message_count=data.get("message_count", 0),
            last_activity=data.get("last_activity", 0.0),
        )


# Keyword routing tables
AGENT_KEYWORDS: dict[AgentDomain, list[str]] = {
    AgentDomain.FINANCE: [
        "invoice", "payment", "balance", "account", "expense", "ledger",
        "xero", "odoo", "quickbooks", "plaid", "bank reconciliation",
        "profit and loss", "balance sheet", "cash flow", "depreciation",
        "accounts payable", "accounts receivable", "audit trail",
    ],
    AgentDomain.HR: [
        "leave", "salary", "onboarding", "pto", "payroll", "employee",
        "headcount", "turnover", "compa ratio", "pay equity", "benefits",
        "performance review", "job description", "offer letter",
        "termination", "resignation",
    ],
    AgentDomain.LEGAL: [
        "contract", "compliance", "nda", "gdpr", "lawsuit", "clause",
        "court", "litigation", "attorney", "privilege", "jurisdiction",
        "statute of limitations", "cease and desist", "demand letter",
        "intellectual property", "trademark", "copyright",
    ],
    AgentDomain.SHARED: [
        "email", "schedule", "meeting", "appointment", "reminder",
        "calendar", "draft", "send email", "availability",
    ],
}


def classify_intent(text: str) -> AgentDomain:
    """Classify message intent based on keyword match. Zero-cost, zero-API-call."""
    text_lower = text.lower()
    scores: dict[AgentDomain, int] = {d: 0 for d in AgentDomain}

    for domain, keywords in AGENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[domain] += 1

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return AgentDomain.GENERAL
    return best


class MessageRouter:
    """Routes WhatsApp messages to specialist agents with session awareness."""

    def __init__(self, settings, redis_client=None, kafka_producer=None):
        self.settings = settings
        self.redis = redis_client
        self.kafka = kafka_producer
        self.session_ttl = 3600

    async def get_session(self, wa_id: str) -> Session:
        """Retrieve session from Redis or create a new one."""
        if self.redis:
            raw = await self.redis.get(f"wa:session:{wa_id}")
            if raw:
                return Session.from_dict(json.loads(raw))
        return Session(wa_id=wa_id)

    async def save_session(self, session: Session):
        """Persist session to Redis."""
        if self.redis:
            session.last_activity = __import__("time").time()
            await self.redis.set(
                f"wa:session:{session.wa_id}",
                json.dumps(session.to_dict()),
                ex=self.session_ttl,
            )

    async def route(self, msg) -> AgentDomain:
        """Route a message and return the target domain."""
        wa_id = msg.from_
        session = await self.get_session(wa_id)

        # If user is mid-conversation with an agent, keep routing there
        if session.active_agent and session.state not in (ConvState.RESOLVED, ConvState.IDLE):
            domain = AgentDomain(session.active_agent)
        else:
            body = msg.text.body if msg.text else ""
            domain = classify_intent(body)
            session.active_agent = domain.value

        session.message_count += 1
        await self.save_session(session)

        # Publish to Kafka for async agent dispatch
        if self.kafka:
            await self.kafka.send("whatsapp.messages", {
                "wa_id": wa_id,
                "message_id": msg.id,
                "domain": domain.value,
                "text": msg.text.body if msg.text else "",
                "session": session.to_dict(),
            })

        logger.info("Message routed", extra={
            "wa_id": wa_id,
            "message_id": msg.id,
            "domain": domain.value,
            "state": session.state.value,
        })

        return domain

    async def set_state(self, wa_id: str, state: ConvState, agent: str | None = None):
        """Manually update session state (called by agents after processing)."""
        session = await self.get_session(wa_id)
        session.transition(state)
        if agent:
            session.active_agent = agent
        await self.save_session(session)

    async def clear_session(self, wa_id: str):
        """Reset a user's session to IDLE."""
        if self.redis:
            await self.redis.delete(f"wa:session:{wa_id}")
        logger.info("Session cleared", extra={"wa_id": wa_id})


# --- Direct agent dispatch (development / no Kafka) ---

async def dispatch_to_agent(domain: AgentDomain, wa_id: str, text: str) -> str:
    """Call the appropriate Digital FTE agent and return its response.

    In production, agents are separate services listening on Kafka.
    This is the synchronous fallback for development.
    """
    import httpx

    agent_endpoints = {
        AgentDomain.FINANCE: "http://localhost:8080/route",
        AgentDomain.HR: "http://localhost:8080/route",
        AgentDomain.LEGAL: "http://localhost:8080/route",
        AgentDomain.SHARED: "http://localhost:8080/route",
    }

    endpoint = agent_endpoints.get(domain)
    if not endpoint:
        return "I couldn't determine which specialist to connect you with. Please try rephrasing."

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(endpoint, json={
                "domain": domain.value,
                "user_id": wa_id,
                "message": text,
            })
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", data.get("message", str(data)))
            logger.warning(f"Agent dispatch failed: {resp.status_code}")
            return f"[{domain.value} agent returned status {resp.status_code}]"
    except Exception as e:
        logger.error(f"Agent dispatch error for {domain.value}: {e}")
        return f"Sorry, the {domain.value} specialist is currently unavailable. Please try again later."


if __name__ == "__main__":
    # Quick test: classify a few sample messages
    samples = [
        "I need to create an invoice for a client",
        "How many vacation days do I have left?",
        "Review this NDA before I sign it",
        "Schedule a meeting with the legal team tomorrow",
        "What's the weather like?",
    ]
    for s in samples:
        domain = classify_intent(s)
        print(f"[{domain.value:8}] {s}")
