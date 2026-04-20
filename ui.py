from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Data Models ──────────────────────────────────────────────
class UserMessage(BaseModel):
    message: str
    user_id: str

# ── In-Memory Database ───────────────────────────────────────
CRM_DB = {
    "leads": [],
    "support_tickets": []
}

# ── FSM State Storage ────────────────────────────────────────
USER_STATE = {}
USER_DATA  = {}

# ── Intent Keywords ──────────────────────────────────────────
LEAD_KEYWORDS    = ["price", "pricing", "cost", "buy", "features", "demo", "sales", "lead"]
SUPPORT_KEYWORDS = ["help", "bug", "broken", "login", "password", "support", "issue", "error"]
RESET_KEYWORDS   = ["hi", "hello", "cancel", "menu", "start over", "restart", "reset"]

EMAIL_REGEX  = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
TICKET_REGEX = re.compile(r"tick-\d+", re.IGNORECASE)

WELCOME = (
    "👋 Welcome to CRM Assistant! I can help you with:\n\n"
    "• 💰 **Pricing & Plans** — ask about our costs\n"
    "• 🎯 **Demo Request** — get a live walkthrough\n"
    "• 🐛 **Bug Reports** — log a support ticket\n"
    "• 🔍 **Ticket Status** — look up a TICK-### ID\n\n"
    "What can I help you with today?"
)

# ── Helper ───────────────────────────────────────────────────
def next_ticket_id():
    return f"TICK-{len(CRM_DB['support_tickets']) + 100}"

# ── Main Chat Endpoint ───────────────────────────────────────
@app.post("/chat")
async def chat(msg: UserMessage):
    uid  = msg.user_id
    text = msg.message.strip()
    low  = text.lower()

    # ── Escape Hatch ─────────────────────────────────────────
    if any(kw in low for kw in RESET_KEYWORDS):
        USER_STATE[uid] = None
        USER_DATA[uid]  = {}
        return {"response": WELCOME}

    state = USER_STATE.get(uid)

    # ═══════════════════════════════════════════════════════
    # STATELESS routing (no active flow)
    # ═══════════════════════════════════════════════════════
    if state is None:

        # Ticket lookup
        match = TICKET_REGEX.search(low)
        if match:
            ticket_id = match.group().upper()
            found = next((t for t in CRM_DB["support_tickets"] if t["ticket"] == ticket_id), None)
            if found:
                return {"response": (
                    f"🎫 **Ticket Found: {found['ticket']}**\n\n"
                    f"**Customer:** {found['name']}\n"
                    f"**Email:** {found['email']}\n"
                    f"**Issue:** {found['issue']}\n"
                    f"**Status:** 🟡 In Progress"
                )}
            else:
                return {"response": f"❌ No ticket found with ID **{ticket_id}**. Please check the ID and try again."}

        # Pricing / Lead intent → show pricing card AND start lead capture
        if any(kw in low for kw in LEAD_KEYWORDS):
            USER_STATE[uid] = "WAITING_FOR_LEAD_NAME"
            USER_DATA[uid]  = {}
            return {"response": (
                "Great question! Here are our plans: [SHOW_PRICING]\n\n"
                "I'd love to connect you with our team for a personalised walkthrough. "
                "Could I get your **name** first?"
            )}

        # Support intent
        if any(kw in low for kw in SUPPORT_KEYWORDS):
            USER_STATE[uid] = "WAITING_FOR_SUPPORT_NAME"
            USER_DATA[uid]  = {}
            return {"response": "I'm sorry to hear you're having trouble. Let me create a support ticket for you.\n\nFirst, what's your **full name**?"}

        # Unknown
        return {"response": (
            "I'm not sure I understood that. " + WELCOME
        )}

    # ═══════════════════════════════════════════════════════
    # LEAD PIPELINE
    # ═══════════════════════════════════════════════════════
    elif state == "WAITING_FOR_LEAD_NAME":
        if len(text.split()) > 3:
            return {"response": "Please enter just your name (first and last name only)."}
        USER_DATA[uid]["name"] = text
        USER_STATE[uid] = "WAITING_FOR_LEAD_EMAIL"
        return {"response": f"Nice to meet you, **{text}**! What's your **email address**?"}

    elif state == "WAITING_FOR_LEAD_EMAIL":
        if not EMAIL_REGEX.search(text):
            return {"response": "That doesn't look like a valid email. Please enter a valid email address (e.g., name@company.com)."}
        USER_DATA[uid]["email"] = text
        name  = USER_DATA[uid]["name"]
        email = USER_DATA[uid]["email"]
        CRM_DB["leads"].append({"name": name, "email": email})
        print(f"[WEBHOOK ALERT] NEW LEAD CAPTURED! Name: {name} | Email: {email}")
        USER_STATE[uid] = None
        USER_DATA[uid]  = {}
        return {"response": (
            f"✅ **Lead registered successfully!**\n\n"
            f"Thanks, **{name}**! Our sales team will reach out to **{email}** shortly.\n\n"
            "Is there anything else I can help you with?"
        )}

    # ═══════════════════════════════════════════════════════
    # SUPPORT PIPELINE
    # ═══════════════════════════════════════════════════════
    elif state == "WAITING_FOR_SUPPORT_NAME":
        if len(text.split()) > 3:
            return {"response": "Please enter just your name (first and last name only)."}
        USER_DATA[uid]["name"] = text
        USER_STATE[uid] = "WAITING_FOR_SUPPORT_EMAIL"
        return {"response": f"Got it, **{text}**. What's your **email address**?"}

    elif state == "WAITING_FOR_SUPPORT_EMAIL":
        if not EMAIL_REGEX.search(text):
            return {"response": "That doesn't look like a valid email. Please try again."}
        USER_DATA[uid]["email"] = text
        USER_STATE[uid] = "WAITING_FOR_SUPPORT_ISSUE"
        return {"response": "Thanks! Now please **describe your issue** in detail so we can help you as quickly as possible."}

    elif state == "WAITING_FOR_SUPPORT_ISSUE":
        ticket_id = next_ticket_id()
        ticket = {
            "ticket": ticket_id,
            "name":   USER_DATA[uid]["name"],
            "email":  USER_DATA[uid]["email"],
            "issue":  text
        }
        CRM_DB["support_tickets"].append(ticket)
        print(f"[TICKET CREATED] {ticket_id} | {ticket['name']} | {ticket['issue']}")
        USER_STATE[uid] = None
        USER_DATA[uid]  = {}
        return {"response": (
            f"🎫 **Support Ticket Created!**\n\n"
            f"**Ticket ID:** `{ticket_id}`\n"
            f"**Issue:** {text}\n\n"
            "Our team will investigate and respond to your email shortly. "
            f"You can check the status anytime by typing your ticket ID: `{ticket_id}`"
        )}

    # Fallback
    USER_STATE[uid] = None
    return {"response": WELCOME}


# ── Admin Endpoint ───────────────────────────────────────────
@app.get("/api/admin")
async def admin():
    return {
        "leads": CRM_DB["leads"],
        "support_tickets": CRM_DB["support_tickets"],
        "stats": {
            "total_leads":   len(CRM_DB["leads"]),
            "total_tickets": len(CRM_DB["support_tickets"])
        }
    }
