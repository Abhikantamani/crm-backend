from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re, random
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ── Request Schema ────────────────────────────────────────────
class UserMessage(BaseModel):
    message: str
    user_id: str
    state:   str  = "IDLE"
    data:    dict = {}

# ── Mock Database ─────────────────────────────────────────────
CRM_DB = {
    "leads":             [],
    "deals":             [],
    "appointments":      [],
    "communication_log": [],
    "support_tickets":   [],
}
LEAD_COUNTER = [784]

# ── Pricing ───────────────────────────────────────────────────
PLANS = {
    "basic":      {"monthly": 8000,  "annual": 76800,  "users": 5,   "label": "Basic"},
    "pro":        {"monthly": 20000, "annual": 192000, "users": 20,  "label": "Pro"},
    "enterprise": {"monthly": 45000, "annual": 432000, "users": 999, "label": "Enterprise"},
}

# ── Regex ─────────────────────────────────────────────────────
EMAIL_RE    = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE    = re.compile(r"[\+]?[\d][\d\s\-]{8,14}\d")
TICK_RE     = re.compile(r"tick-\d+", re.IGNORECASE)
NUM_RE      = re.compile(r"\b(\d+)\b")
ONLY_NUM_RE = re.compile(r"^\s*\d+\s*$")

# ── Intent keywords ───────────────────────────────────────────
# "greeting" and "reset" use WHOLE-WORD matching (see detect_intent)
INTENT_MAP = {
    "greeting":          ["hi", "hello", "hey", "good morning", "good evening", "namaste", "start"],
    "reset":             ["cancel", "start over", "restart", "reset", "menu", "main menu"],
    "pricing":           ["price", "pricing", "pricings", "cost", "plan", "plans", "package",
                          "how much", "rate", "fees", "charge", "basic", "pro", "enterprise"],
    "demo":              ["demo", "demonstration", "walkthrough", "trial", "book a demo", "schedule demo", "i want a demo"],
    "buy":               ["buy", "purchase", "subscribe", "sign up", "get started", "i want to buy"],
    "feature":           ["feature", "features", "what can", "capability", "capabilities", "what does it do"],
    "support":           ["bug", "error", "broken", "issue", "problem", "not working", "support",
                          "login problem", "password", "raise a ticket", "support ticket",
                          "got a bug", "i got a bug", "i have a bug", "i need help", "help me"],
    "ticket_lookup":     ["tick-"],
    "objection_budget":  ["expensive", "costly", "too much", "high price", "cheaper", "discount", "afford"],
    "objection_compete": ["competitor", "salesforce", "hubspot", "zoho", "freshsales", "other crm"],
    "objection_timing":  ["not now", "later", "next month", "next quarter", "not ready"],
    "closing_yes":       ["yes", "sure", "okay", "ok", "proceed", "go ahead", "confirm", "let's do", "sounds good"],
    "closing_no":        ["nope", "not interested", "maybe later", "goodbye", "exit", "bye"],
    "lead_score":        ["lead score", "my score", "what is my score", "my lead score"],
    "next_action":       ["next best action", "what should i do", "next step", "recommendation", "suggest"],
    "automation":        ["trigger automation", "automation", "workflow", "automate"],
    "whatsapp":          ["whatsapp", "send on whatsapp", "send details", "send to whatsapp"],
    "proposal":          ["proposal", "send proposal", "get proposal", "send me a proposal"],
    "create_deal":       ["create deal", "create a deal", "add deal", "make deal", "add to pipeline"],
    "thank_you":         ["thank you", "thanks", "thank"],
    "contact_info":      ["my name is", "email is", "phone is", "company is"],
}

WHOLE_WORD_INTENTS = {"greeting", "reset"}

def detect_intent(low: str) -> str:
    for intent, keywords in INTENT_MAP.items():
        for kw in keywords:
            if intent in WHOLE_WORD_INTENTS:
                if re.search(r'\b' + re.escape(kw) + r'\b', low):
                    return intent
            else:
                if kw in low:
                    return intent
    return "unknown"

# ── Helpers ───────────────────────────────────────────────────
def extract_plan(low: str) -> str:
    if "enterprise" in low: return "enterprise"
    if "pro"        in low: return "pro"
    if "basic"      in low: return "basic"
    return None

def extract_team_size(low: str) -> str:
    m = NUM_RE.search(low)
    return m.group(1) if m else None

def fmt_inr(amount: int) -> str:
    return f"₹{amount/100000:.1f} Lakhs" if amount >= 100000 else f"₹{amount:,}"

def calc_lead_score(data: dict) -> int:
    score = 40
    if data.get("name"):    score += 10
    if data.get("email"):   score += 15
    if data.get("phone"):   score += 8
    if data.get("company"): score += 10
    if data.get("team_size"):
        ts = int(str(data["team_size"]).strip())
        score += 5 if ts < 10 else (10 if ts < 50 else 17)
    if data.get("plan") == "enterprise": score += 10
    elif data.get("plan") == "pro":      score += 6
    if data.get("demo_booked"):  score += 8
    if data.get("deal_created"): score += 5
    return min(score, 100)

def score_label(score: int) -> str:
    if score >= 80: return "🔥 Hot"
    if score >= 60: return "🌡️ Warm"
    return "❄️ Cold"

def save_lead(data: dict) -> str:
    # Don't duplicate leads for same session
    lid = f"lead_{LEAD_COUNTER[0]}"
    LEAD_COUNTER[0] += 1
    score = calc_lead_score(data)
    CRM_DB["leads"].append({
        **data, "lead_id": lid, "lead_score": score,
        "stage": "New", "created": datetime.now().strftime("%d %b %Y %H:%M")
    })
    return lid

def save_deal(data: dict, value: int) -> str:
    did = f"deal_{random.randint(100, 999)}"
    CRM_DB["deals"].append({
        "deal_id": did, "name": data.get("name", "Unknown"),
        "company": data.get("company", "—"), "value": value,
        "plan": data.get("plan", "—"), "stage": "Proposal",
        "probability": 75, "created": datetime.now().strftime("%d %b %Y")
    })
    return did

def save_ticket(data: dict, issue: str) -> str:
    tid = f"TICK-{len(CRM_DB['support_tickets']) + 100}"
    CRM_DB["support_tickets"].append({
        "ticket": tid, "name": data.get("name", "—"),
        "email": data.get("email", "—"), "issue": issue, "status": "Open"
    })
    return tid

def book_appointment(data: dict) -> dict:
    demo_date = (datetime.now() + timedelta(days=random.randint(2, 5))).strftime("%A, %d %B")
    aid = f"apt_{random.randint(100, 999)}"
    apt = {
        "id": aid, "name": data.get("name", "—"),
        "email": data.get("email", "—"), "date": demo_date,
        "time": "11:00 AM", "meet": f"https://meet.google.com/crm-{aid}"
    }
    CRM_DB["appointments"].append(apt)
    return apt

def log_comm(data: dict, channel: str, note: str):
    CRM_DB["communication_log"].append({
        "name": data.get("name", "—"), "channel": channel,
        "note": note, "time": datetime.now().strftime("%d %b %Y %H:%M")
    })

def reply(text: str, state: str = "IDLE", data: dict = None):
    return {"response": text, "state": state, "data": data or {}}

# ── Static messages ───────────────────────────────────────────
WELCOME = (
    "👋 Hello! I'm your **AI Sales Assistant** for NexCRM.\n\n"
    "I can help you with:\n"
    "• 💰 **Pricing & Plans** — find the right package\n"
    "• 🎯 **Book a Demo** — see NexCRM in action\n"
    "• 📋 **Proposal or Deal** — get a custom quote\n"
    "• 🐛 **Support Ticket** — report an issue\n"
    "• 🤖 **Features** — learn what NexCRM can do\n\n"
    "What can I help you with today?"
)

FEATURES = (
    "🚀 **NexCRM — Full Feature List:**\n\n"
    "• 🎯 Lead Management & AI Scoring\n"
    "• 📞 Contact Management & Customer 360 View\n"
    "• 💼 Deal / Sales Pipeline & Forecasting\n"
    "• 📊 Dashboard, KPIs & Real-time Reports\n"
    "• 📅 Tasks, Calendar & Auto-scheduling\n"
    "• 💬 WhatsApp & Email Communication Logs\n"
    "• ⚡ Workflow Automation & Triggers\n"
    "• 🤖 Predictive Lead Scoring (AI)\n"
    "• 📈 Marketing Automation & Campaigns\n"
    "• 🎫 Support Ticket Management\n\n"
    "All plans include a **30-day free trial**.\n\n"
    "Would you like **pricing**, a **demo**, or more details on any feature?"
)

# ═══════════════════════════════════════════════════════════════
# MAIN ENDPOINT
# ═══════════════════════════════════════════════════════════════
@app.post("/chat")
async def chat(msg: UserMessage):
    raw    = msg.message.strip()
    low    = raw.lower()
    state  = msg.state
    data   = dict(msg.data)
    intent = detect_intent(low)

    # ── Global reset ──────────────────────────────────────────
    if intent == "reset":
        return reply(WELCOME)

    # ── Greeting mid-flow → soft reset ───────────────────────
    if intent == "greeting" and state != "IDLE":
        return reply(WELCOME)

    # ── Goodbye ───────────────────────────────────────────────
    if intent == "closing_no" and state == "IDLE":
        name = data.get("name", "")
        return reply(
            f"Thank you{', ' + name if name else ''}! 😊\n\n"
            "It was a pleasure chatting with you. Our team will be in touch soon.\n\n"
            "Feel free to come back anytime! 👋"
        )

    # ── Thank you ─────────────────────────────────────────────
    if intent == "thank_you":
        score = calc_lead_score(data)
        return reply(
            "You're welcome! 🙌\n\n"
            + (f"Your lead score: **{score}/100** — {score_label(score)}. Our sales team has been notified.\n\n"
               if data.get("name") else "")
            + "Is there anything else I can help you with?"
        )

    # ══════════════════════════════════════════════════════════
    # STATEFUL FLOWS
    # ══════════════════════════════════════════════════════════

    # ── Lead name ─────────────────────────────────────────────
    if state == "LEAD_NAME":
        if len(raw.split()) > 4:
            return reply("Please enter just your name (e.g. Priya Sharma).", "LEAD_NAME", data)
        data["name"] = raw
        score = calc_lead_score(data)
        return reply(
            f"Nice to meet you, **{raw}**! 👋\n"
            f"Lead score so far: **{score}/100**\n\n"
            "What's your **email address**?",
            "LEAD_EMAIL", data
        )

    # ── Lead email ────────────────────────────────────────────
    if state == "LEAD_EMAIL":
        if not EMAIL_RE.search(raw):
            return reply(
                "That doesn't look like a valid email. Please try again (e.g. priya@techsolutions.com).",
                "LEAD_EMAIL", data
            )
        data["email"] = raw
        score = calc_lead_score(data)
        return reply(
            f"✅ Email saved! Lead score: **{score}/100**\n\n"
            "What's your **company name**? *(or type 'skip')*",
            "LEAD_COMPANY", data
        )

    # ── Lead company ──────────────────────────────────────────
    if state == "LEAD_COMPANY":
        if raw.lower() != "skip":
            data["company"] = raw
        score = calc_lead_score(data)
        lid   = save_lead(data)
        plan  = data.get("plan", "pro")
        p     = PLANS.get(plan, PLANS["pro"])
        return reply(
            f"✅ **Contact updated!**\n"
            f"✅ **Lead linked to {data.get('company', 'your company')}**\n\n"
            f"• Lead ID: `{lid}`\n"
            f"• Lead Score: **{score}/100** — {score_label(score)}\n\n"
            "What would you like to do next?\n\n"
            "• **Book a demo** — personalised walkthrough\n"
            "• **Get a proposal** — detailed quote by email\n"
            "• **Create a deal** — add to our pipeline",
            "POST_LEAD", data
        )

    # ── Book demo confirmation ────────────────────────────────
    if state == "BOOK_DEMO":
        apt   = book_appointment(data)
        data["demo_booked"] = True
        log_comm(data, "System", f"Demo booked for {apt['date']}")
        score = calc_lead_score(data)
        return reply(
            f"🎉 **Demo Scheduled Successfully!**\n\n"
            f"✅ Task created: Demo with **{data.get('name', 'you')}**\n"
            f"✅ Date: **{apt['date']} at {apt['time']}**\n"
            f"✅ Google Meet: `{apt['meet']}`\n"
            f"✅ Calendar invite sent to **{data.get('email', 'your email')}**\n\n"
            f"Lead Score updated: **{score}/100** — {score_label(score)}\n\n"
            "Would you like me to **create the deal** or **send the proposal** now?",
            "POST_DEMO", data
        )

    # ── Support: name ─────────────────────────────────────────
    if state == "SUPPORT_NAME":
        if len(raw.split()) > 4:
            return reply("Please enter just your name (e.g. Rahul Verma).", "SUPPORT_NAME", data)
        data["name"] = raw
        return reply(
            f"Got it, **{raw}**. What's your **email address**?",
            "SUPPORT_EMAIL", data
        )

    # ── Support: email ────────────────────────────────────────
    if state == "SUPPORT_EMAIL":
        if not EMAIL_RE.search(raw):
            return reply("Please enter a valid email address.", "SUPPORT_EMAIL", data)
        data["email"] = raw
        return reply(
            "Thank you! Please **describe your issue** in as much detail as possible.",
            "SUPPORT_ISSUE", data
        )

    # ── Support: issue ────────────────────────────────────────
    if state == "SUPPORT_ISSUE":
        tid = save_ticket(data, raw)
        return reply(
            f"🎫 **Support Ticket Created!**\n\n"
            f"• Ticket ID: `{tid}`\n"
            f"• Issue: {raw}\n"
            f"• Status: 🟡 Open\n\n"
            f"Our support team will respond to **{data.get('email', 'your email')}** within 24 hours.\n\n"
            f"You can check your ticket status anytime by typing: `{tid}`"
        )

    # ── Post lead actions ─────────────────────────────────────
    if state == "POST_LEAD":
        if "demo" in low or (intent == "closing_yes" and not data.get("demo_booked")):
            return reply(
                f"Perfect! Let me book that for you, **{data.get('name', '')}**.\n\nConfirming your slot...",
                "BOOK_DEMO", data
            )
        if "proposal" in low or intent == "proposal":
            plan = data.get("plan", "pro")
            p    = PLANS.get(plan, PLANS["pro"])
            log_comm(data, "Email", "Proposal sent")
            return reply(
                f"📄 **Proposal Sent!**\n\n"
                f"✅ Emailed to **{data.get('email', 'you')}**\n\n"
                f"• Plan: **{p['label']}**\n"
                f"• Monthly: **₹{p['monthly']:,}**\n"
                f"• Annual: **₹{p['annual']:,}** *(save 20%)*\n"
                f"• Users: Up to **{p['users']}** users\n\n"
                "Would you like to **book a demo** or **create the deal**?",
                "POST_LEAD", data
            )
        if "deal" in low or intent == "create_deal":
            plan  = data.get("plan", "pro")
            p     = PLANS.get(plan, PLANS["pro"])
            did   = save_deal(data, p["monthly"])
            score = calc_lead_score(data)
            return reply(
                f"💼 **Deal Created Successfully!**\n\n"
                f"✅ Deal ID: `{did}`\n"
                f"• Value: **₹{p['monthly']:,}/month**\n"
                f"• Stage: **Proposal** | Probability: **75%**\n\n"
                f"Lead Score: **{score}/100** — {score_label(score)}\n\n"
                "Our sales team will follow up shortly. Is there anything else I can help you with?"
            )
        return reply(
            "What would you like to do next?\n\n"
            "• **book demo** — personalised walkthrough\n"
            "• **proposal** — receive a detailed quote\n"
            "• **create deal** — add to our pipeline",
            "POST_LEAD", data
        )

    # ── Post demo actions ─────────────────────────────────────
    if state == "POST_DEMO":
        if "deal" in low or intent == "create_deal":
            plan  = data.get("plan", "pro")
            p     = PLANS.get(plan, PLANS["pro"])
            did   = save_deal(data, p["monthly"])
            data["deal_created"] = True
            score = calc_lead_score(data)
            return reply(
                f"💼 **Deal Created!**\n\n"
                f"✅ Deal ID: `{did}`\n"
                f"• Value: **₹{p['monthly']:,}/month**\n"
                f"• Stage: **Proposal** | Probability: **75%**\n\n"
                f"Lead Score: **{score}/100** — {score_label(score)}\n\n"
                "Our sales team will be in touch shortly. Is there anything else I can help you with?",
                "IDLE", data
            )
        if "proposal" in low or intent == "proposal":
            plan = data.get("plan", "pro")
            p    = PLANS.get(plan, PLANS["pro"])
            log_comm(data, "Email", "Proposal sent")
            return reply(
                f"📄 **Proposal Sent to {data.get('email', 'you')}!**\n\n"
                f"• Plan: **{p['label']}**\n"
                f"• Monthly: **₹{p['monthly']:,}**\n"
                f"• Annual: **₹{p['annual']:,}** *(2 months free)*\n\n"
                "Type **'create deal'** whenever you're ready to proceed!",
                "POST_DEMO", data
            )
        return reply(
            "What would you like to do next?\n\n"
            "• **create deal** — add to pipeline\n"
            "• **proposal** — email the quote",
            "POST_DEMO", data
        )

    # ══════════════════════════════════════════════════════════
    # STATELESS INTENT ROUTING
    # ══════════════════════════════════════════════════════════

    if intent == "greeting":
        return reply(WELCOME)

    if intent == "feature":
        return reply(FEATURES)

    # Ticket lookup
    if intent == "ticket_lookup":
        m = TICK_RE.search(low)
        if m:
            tid   = m.group().upper()
            found = next((t for t in CRM_DB["support_tickets"] if t["ticket"] == tid), None)
            if found:
                return reply(
                    f"🎫 **Ticket: {found['ticket']}**\n\n"
                    f"• Customer: **{found['name']}**\n"
                    f"• Email: {found['email']}\n"
                    f"• Issue: {found['issue']}\n"
                    f"• Status: 🟡 **In Progress**"
                )
            return reply(f"❌ No ticket found with ID **{tid}**. Please double-check the ID and try again.")

    # Support
    if intent == "support":
        return reply(
            "I'm sorry to hear you're having trouble. Let me raise a support ticket for you.\n\n"
            "First, what's your **full name**?",
            "SUPPORT_NAME", data
        )

    # Lead score
    if intent == "lead_score":
        score = calc_lead_score(data)
        return reply(
            f"🎯 **Your Lead Score: {score}/100** — {score_label(score)}\n\n"
            + ("Our sales team has been notified and will reach out shortly!" if score >= 70
               else "Share more details or book a demo to improve your score!")
        )

    # Next best action
    if intent == "next_action":
        if not data.get("name"):
            action = "Share your contact details to get a personalised quote"
        elif not data.get("demo_booked"):
            action = "Book a demo — prospects who attend convert 3x more often"
        elif not data.get("deal_created"):
            action = "Create a deal to lock in pricing and move to proposal stage"
        else:
            action = "Follow up with the proposal and schedule a closing call"
        return reply(f"🤖 **AI Recommendation — Next Best Action:**\n\n➡️ **{action}**")

    # WhatsApp
    if intent == "whatsapp":
        log_comm(data, "WhatsApp", "Details sent via WhatsApp")
        plan = data.get("plan", "pro")
        p    = PLANS.get(plan, PLANS["pro"])
        return reply(
            f"📱 **Details Sent on WhatsApp!**\n\n"
            f"✅ Message delivered to your registered number\n\n"
            f"• Plan: **{p['label']}** — ₹{p['monthly']:,}/month\n"
            f"• Reply **YES** to confirm your demo slot\n\n"
            "Is there anything else I can help you with?"
        )

    # Automation
    if intent == "automation":
        return reply(
            "⚡ **Automation Triggered!**\n\n"
            "✅ Lead nurture sequence started\n"
            "✅ Follow-up email scheduled for tomorrow at 10:00 AM\n"
            "✅ Sales manager notified via Slack\n"
            "✅ Task created: Follow-up call within 24 hours\n\n"
            "Our automated workflow is now running in the background!"
        )

    # Proposal (stateless)
    if intent == "proposal":
        if not data.get("name"):
            return reply(
                "I'd be happy to send you a detailed proposal! Could I get your **name** first?",
                "LEAD_NAME", data
            )
        plan = data.get("plan", "pro")
        p    = PLANS.get(plan, PLANS["pro"])
        log_comm(data, "Email", "Proposal sent")
        return reply(
            f"📄 **Proposal Sent!**\n\n"
            f"✅ Emailed to **{data.get('email', 'your email')}**\n\n"
            f"• Plan: **{p['label']}** — ₹{p['monthly']:,}/month\n"
            f"• Annual: ₹{p['annual']:,} *(save 20%)*\n\n"
            "Type **'create deal'** whenever you're ready to proceed!"
        )

    # Create deal (stateless)
    if intent == "create_deal":
        if not data.get("name"):
            return reply(
                "Let me set that up for you! What's your **name** first?",
                "LEAD_NAME", data
            )
        plan  = data.get("plan", "pro")
        p     = PLANS.get(plan, PLANS["pro"])
        did   = save_deal(data, p["monthly"])
        score = calc_lead_score(data)
        return reply(
            f"💼 **Deal Created!**\n\n"
            f"✅ Deal ID: `{did}`\n"
            f"• Value: **₹{p['monthly']:,}/month**\n"
            f"• Stage: **Proposal** | Probability: **75%**\n\n"
            f"Lead Score: **{score}/100** — {score_label(score)}\n\n"
            "Our sales team will follow up shortly!"
        )

    # Objection: budget
    if intent == "objection_budget":
        plan = data.get("plan", "pro")
        p    = PLANS.get(plan, PLANS["pro"])
        return reply(
            "I completely understand — budget is always a key consideration! Here's how we make it work:\n\n"
            f"💡 **Annual billing saves 20%** — just ₹{p['annual']:,}/year\n"
            f"💡 **Proven ROI** — most clients recover the cost within the first month\n"
            f"💡 **Start small** — Basic plan at ₹8,000/month, upgrade anytime\n"
            f"💡 **Free trial** — 30 days, no credit card required\n\n"
            "Would you like a **custom quote** or to speak directly with our team?"
        )

    # Objection: competition
    if intent == "objection_compete":
        return reply(
            "Great question! Here's how NexCRM stands out:\n\n"
            "• **vs Salesforce** — 60% lower cost with the same enterprise-grade features\n"
            "• **vs HubSpot** — No per-user pricing trap, unlimited contacts on all plans\n"
            "• **vs Zoho** — Superior AI lead scoring + dedicated Indian support team\n\n"
            "Plus a **free 30-day trial** — no commitment needed.\n\n"
            "Would you like to book a **comparison demo**?"
        )

    # Objection: timing
    if intent == "objection_timing":
        return reply(
            "Totally understood — timing matters! Here are your options:\n\n"
            "• 📅 **Lock in current pricing** — rates are increasing next quarter\n"
            "• 🔔 **Schedule a reminder** — I'll have our team follow up next month\n"
            "• 📄 **Receive the proposal** — review it at your own pace\n\n"
            "What works best for you?"
        )

    # Contact info passive capture
    if intent == "contact_info":
        email_m = EMAIL_RE.search(raw)
        phone_m = PHONE_RE.search(raw)
        if email_m: data["email"] = email_m.group()
        if phone_m: data["phone"] = phone_m.group()
        if "my name is" in low:
            name_part = re.sub(r".*my name is\s*", "", low).strip().title()
            if name_part: data["name"] = name_part
        if "company is" in low:
            co_part = re.sub(r".*company is\s*", "", low).strip().title()
            if co_part: data["company"] = co_part
        score = calc_lead_score(data)
        parts = []
        if data.get("name"):    parts.append(f"Name: **{data['name']}**")
        if data.get("email"):   parts.append(f"Email: **{data['email']}**")
        if data.get("company"): parts.append(f"Company: **{data['company']}**")
        if data.get("name") and data.get("email"):
            lid = save_lead(data)
            return reply(
                "✅ **Contact Details Updated!**\n\n"
                + "\n".join(f"✅ {p}" for p in parts) + "\n\n"
                f"✅ Lead linked to {data.get('company', 'your account')}\n"
                f"🎯 Lead Score: **{score}/100** — {score_label(score)}\n\n"
                "Shall I book a **personalised demo** for next week?",
                "POST_LEAD", data
            )
        return reply(
            "Thanks for sharing! " + " | ".join(parts) + "\n\n"
            "Could you also share your " +
            ("**email address**?" if not data.get("email") else "**company name**?"),
            "IDLE", data
        )

    # Pricing
    if intent == "pricing":
        plan      = extract_plan(low)
        team_size = extract_team_size(low)

        if plan and team_size:
            data["plan"]      = plan
            data["team_size"] = team_size
            p     = PLANS[plan]
            score = calc_lead_score(data)
            lid   = save_lead(data) if data.get("name") else None
            return reply(
                f"Great choice! The **{p['label']} plan** for **{team_size} users** starts at:\n\n"
                f"• 💰 Monthly: **₹{p['monthly']:,}/month**\n"
                f"• 💰 Annual: **₹{p['annual']:,}/year** *(save 20%)*\n\n"
                "Includes: Unlimited storage, priority support, custom integrations, AI features & dedicated account manager.\n\n"
                + (f"✅ Lead created *(ID: `{lid}`)*\n" if lid else "")
                + f"✅ Deal added to pipeline *(₹{p['monthly']:,} monthly)*\n"
                + f"🎯 Lead Score: **{score}/100** — {score_label(score)}\n\n"
                "Would you like to **book a demo**, get the **proposal**, or **customise** for annual billing?",
                "POST_LEAD", data
            )

        if plan:
            data["plan"] = plan
            p = PLANS[plan]
            return reply(
                f"**{p['label']} Plan** — ₹{p['monthly']:,}/month *(₹{p['annual']:,}/year)*\n\n"
                f"Includes up to **{p['users']} users**, full CRM access, and dedicated onboarding.\n\n"
                "How many **team members** will be using NexCRM?",
                "IDLE", data
            )

        return reply(
            "💰 **NexCRM Pricing Plans:**\n\n"
            "| Plan | Monthly | Annual | Users |\n"
            "|------|---------|--------|-------|\n"
            "| Basic | ₹8,000 | ₹76,800 | Up to 5 |\n"
            "| Pro | ₹20,000 | ₹1,92,000 | Up to 20 |\n"
            "| Enterprise | ₹45,000 | ₹4,32,000 | Unlimited |\n\n"
            "All plans include a **30-day free trial** and dedicated onboarding.\n\n"
            "Which plan interests you? Or tell me your **team size** and I'll recommend the best fit!",
            "IDLE", data
        )

    # Demo
    if intent == "demo":
        if not data.get("name"):
            return reply(
                "I'd love to schedule a personalised demo for you! 🎯\n\n"
                "First, could I get your **name**?",
                "LEAD_NAME", data
            )
        return reply(
            f"Let me book that for you, **{data['name']}**!\n\nConfirming your slot for next week...",
            "BOOK_DEMO", data
        )

    # Buy
    if intent == "buy":
        if not data.get("name"):
            return reply(
                "Excellent! Let's get you started with NexCRM! 🚀\n\n"
                "First, could I get your **name**?",
                "LEAD_NAME", data
            )
        plan  = data.get("plan", "pro")
        p     = PLANS.get(plan, PLANS["pro"])
        did   = save_deal(data, p["monthly"])
        score = calc_lead_score(data)
        return reply(
            f"🎉 **Amazing — let's get started!**\n\n"
            f"✅ Deal created: `{did}`\n"
            f"• Plan: **{p['label']}** at ₹{p['monthly']:,}/month\n"
            f"• Lead Score: **{score}/100** — {score_label(score)}\n\n"
            "Our onboarding team will contact you within **2 business hours**!\n\n"
            "Would you like to book your **kickoff call** now?"
        )

    # Standalone number → team size recommendation
    if ONLY_NUM_RE.match(low):
        ts     = low.strip()
        ts_int = int(ts)
        data["team_size"] = ts
        plan = data.get("plan")
        if not plan:
            if ts_int <= 5:
                plan = "basic"
            elif ts_int <= 20:
                plan = "pro"
            else:
                plan = "enterprise"
            data["plan"] = plan
        p     = PLANS[plan]
        score = calc_lead_score(data)
        return reply(
            f"For a team of **{ts}**, I recommend the **{p['label']} Plan**:\n\n"
            f"• Monthly: **₹{p['monthly']:,}**\n"
            f"• Annual: **₹{p['annual']:,}** *(save 20%)*\n"
            f"• Users: Up to **{p['users']}** users\n\n"
            f"🎯 Estimated Lead Score: **{score}/100**\n\n"
            "Would you like to **book a demo**, get a **proposal**, or **customise** the quote?",
            "POST_LEAD", data
        )

    # Unknown
    return reply(
        "I didn't quite catch that — I'm here to help with:\n\n"
        "• **Pricing** — ask about our plans\n"
        "• **Demo** — book a live walkthrough\n"
        "• **Support** — raise a ticket\n"
        "• **Features** — learn what NexCRM offers\n\n"
        "What would you like to do?"
    )


# ── Admin API (used by AdminDashboard.jsx only) ───────────────
@app.get("/api/admin")
async def admin():
    return {
        "leads":             CRM_DB["leads"],
        "support_tickets":   CRM_DB["support_tickets"],
        "deals":             CRM_DB["deals"],
        "appointments":      CRM_DB["appointments"],
        "communication_log": CRM_DB["communication_log"],
        "stats": {
            "total_leads":    len(CRM_DB["leads"]),
            "total_tickets":  len(CRM_DB["support_tickets"]),
            "total_deals":    len(CRM_DB["deals"]),
            "pipeline_value": sum(d["value"] for d in CRM_DB["deals"]),
        }
    }