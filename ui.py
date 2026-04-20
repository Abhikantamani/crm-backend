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

class UserMessage(BaseModel):
    message: str
    user_id: str
    state: str = "IDLE"
    data: dict = {}

CRM_DB = {"leads": [], "support_tickets": []}

EMAIL_REGEX = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
TICKET_REGEX = re.compile(r"tick-\d+", re.IGNORECASE)

LEAD_KEYWORDS    = ["price","pricing","cost","buy","features","demo","sales","lead"]
SUPPORT_KEYWORDS = ["help","bug","broken","login","password","support","issue","error"]
RESET_KEYWORDS   = ["hi","hello","cancel","menu","start over","restart","reset"]

WELCOME = "👋 Welcome to CRM Assistant! I can help you with:\n\n• 💰 **Pricing & Plans** — ask about our costs\n• 🎯 **Demo Request** — get a live walkthrough\n• 🐛 **Bug Reports** — log a support ticket\n• 🔍 **Ticket Status** — look up a TICK-### ID\n\nWhat can I help you with today?"

def reply(text, state="IDLE", data={}):
    return {"response": text, "state": state, "data": data}

@app.post("/chat")
async def chat(msg: UserMessage):
    text  = msg.message.strip()
    low   = text.lower()
    state = msg.state
    data  = dict(msg.data)

    if any(re.search(r'\b' + kw + r'\b', low) for kw in RESET_KEYWORDS):
        return reply(WELCOME)

    if state == "IDLE":
        match = TICKET_REGEX.search(low)
        if match:
            tid = match.group().upper()
            found = next((t for t in CRM_DB["support_tickets"] if t["ticket"] == tid), None)
            if found:
                return reply(f"🎫 **{found['ticket']}**\n**Customer:** {found['name']}\n**Issue:** {found['issue']}\n**Status:** 🟡 In Progress")
            return reply(f"❌ No ticket found with ID **{tid}**.")

        if any(kw in low for kw in LEAD_KEYWORDS):
            return reply("Great question! Here are our plans: [SHOW_PRICING]\n\nI'd love to connect you with our team. Could I get your **name** first?", "LEAD_NAME", {})

        if any(kw in low for kw in SUPPORT_KEYWORDS):
            return reply("I'm sorry to hear that. Let me create a support ticket.\n\nFirst, what's your **full name**?", "SUPPORT_NAME", {})

        return reply("I'm not sure I understood that.\n\n" + WELCOME)

    elif state == "LEAD_NAME":
        if len(text.split()) > 3:
            return reply("Please enter just your name (first and last only).", "LEAD_NAME", data)
        data["name"] = text
        return reply(f"Nice to meet you, **{text}**! What's your **email address**?", "LEAD_EMAIL", data)

    elif state == "LEAD_EMAIL":
        if not EMAIL_REGEX.search(text):
            return reply("That doesn't look valid. Please enter a proper email (e.g., name@company.com).", "LEAD_EMAIL", data)
        data["email"] = text
        CRM_DB["leads"].append({"name": data["name"], "email": data["email"]})
        print(f"[WEBHOOK] NEW LEAD: {data['name']} | {data['email']}")
        return reply(f"✅ **Lead registered!**\n\nThanks **{data['name']}**, our team will reach out to **{data['email']}** shortly.\n\nAnything else I can help with?")

    elif state == "SUPPORT_NAME":
        if len(text.split()) > 3:
            return reply("Please enter just your name.", "SUPPORT_NAME", data)
        data["name"] = text
        return reply(f"Got it, **{text}**. What's your **email address**?", "SUPPORT_EMAIL", data)

    elif state == "SUPPORT_EMAIL":
        if not EMAIL_REGEX.search(text):
            return reply("That doesn't look valid. Please try again.", "SUPPORT_EMAIL", data)
        data["email"] = text
        return reply("Thanks! Now please **describe your issue** in detail.", "SUPPORT_ISSUE", data)

    elif state == "SUPPORT_ISSUE":
        tid = f"TICK-{len(CRM_DB['support_tickets']) + 100}"
        CRM_DB["support_tickets"].append({"ticket": tid, "name": data["name"], "email": data["email"], "issue": text})
        print(f"[TICKET] {tid} | {data['name']} | {text}")
        return reply(f"🎫 **Ticket Created: `{tid}`**\n\n**Issue:** {text}\n\nOur team will respond to your email shortly. Check status anytime with your ticket ID.")

    return reply(WELCOME)

@app.get("/api/admin")
async def admin():
    return {"leads": CRM_DB["leads"], "support_tickets": CRM_DB["support_tickets"],
            "stats": {"total_leads": len(CRM_DB["leads"]), "total_tickets": len(CRM_DB["support_tickets"])}}