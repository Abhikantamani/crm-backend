from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re, random
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ─────────────────────────────────────────────────────────────
# REQUEST SCHEMA
# ─────────────────────────────────────────────────────────────
class UserMessage(BaseModel):
    message: str
    user_id: str
    state:   str  = "IDLE"
    data:    dict = {}

# ─────────────────────────────────────────────────────────────
# MOCK DATABASE
# ─────────────────────────────────────────────────────────────
CRM_DB = {
    "leads":             [],
    "deals":             [],
    "contacts":          [],
    "tasks":             [],
    "appointments":      [],
    "communication_log": [],
    "support_tickets":   [],
    "activities":        [],
}
LEAD_COUNTER = [784]
TICKET_COUNTER = [100]

# ─────────────────────────────────────────────────────────────
# PRICING
# ─────────────────────────────────────────────────────────────
PLANS = {
    "basic":      {"monthly": 8000,  "annual": 76800,  "users": 5,   "label": "Basic"},
    "pro":        {"monthly": 20000, "annual": 192000, "users": 20,  "label": "Pro"},
    "enterprise": {"monthly": 45000, "annual": 432000, "users": 999, "label": "Enterprise"},
}

# ─────────────────────────────────────────────────────────────
# REGEX
# ─────────────────────────────────────────────────────────────
EMAIL_RE    = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE    = re.compile(r"[\+]?[\d][\d\s\-]{8,13}\d")
TICKET_RE   = re.compile(r"tick-\d+", re.IGNORECASE)
NUM_RE      = re.compile(r"\b(\d+)\b")
ONLY_NUM_RE = re.compile(r"^\s*\d+\s*$")

# ─────────────────────────────────────────────────────────────
# INTENT MAP
# greeting + reset use WHOLE-WORD matching to prevent
# "abhi" from matching "hi", "abhiram" from matching "hi" etc.
# ─────────────────────────────────────────────────────────────
INTENT_MAP = {
    # ── Whole-word matched ──
    "greeting": ["hi", "hello", "hey", "good morning", "good afternoon",
                 "good evening", "namaste", "start", "begin"],
    "reset":    ["cancel", "start over", "restart", "reset", "main menu", "go back"],

    # ── Substring matched ──
    "pricing":           ["price", "pricing", "pricings", "cost", "costs", "how much",
                          "rate", "fees", "charges", "package", "packages",
                          "basic plan", "pro plan", "enterprise plan",
                          "basic", "pro plan", "enterprise"],
    "plan_basic":        ["basic"],
    "plan_pro":          ["pro"],
    "plan_enterprise":   ["enterprise"],
    "demo":              ["demo", "demonstration", "walkthrough", "book a demo",
                          "schedule demo", "i want a demo", "show me", "live demo",
                          "book demo", "trial"],
    "buy":               ["buy", "purchase", "subscribe", "sign up", "get started",
                          "i want to buy", "i want to purchase"],
    "feature":           ["feature", "features", "what can", "capability",
                          "capabilities", "what does it", "what do you offer",
                          "what is crm", "tell me about", "modules"],
    "contact_info":      ["my name is", "email is", "phone is", "company is",
                          "i am", "i'm from", "my email", "my phone"],
    "support":           ["bug", "error", "broken", "issue", "problem",
                          "not working", "support ticket", "raise a ticket",
                          "login problem", "password reset", "i need help",
                          "i have a bug", "i got a bug", "got a bug",
                          "i found a bug", "not loading", "failing"],
    "ticket_lookup":     ["tick-"],
    "objection_budget":  ["expensive", "costly", "too much", "high price",
                          "cheaper", "discount", "can't afford", "seems expensive",
                          "it seems expensive", "too costly", "reduce price",
                          "lower price", "budget", "afford"],
    "objection_compete": ["competitor", "salesforce", "hubspot", "zoho",
                          "freshsales", "other crm", "already using",
                          "we use", "compared to"],
    "objection_timing":  ["not now", "later", "next month", "next quarter",
                          "not ready", "in the future", "some other time"],
    "closing_yes":       ["yes", "sure", "okay", "ok", "proceed", "go ahead",
                          "confirm", "let's do it", "sounds good", "absolutely",
                          "definitely", "of course"],
    "closing_no":        ["nope", "not interested", "maybe later",
                          "goodbye", "exit", "bye", "no thanks", "no thank you"],
    "lead_score":        ["lead score", "my score", "what is my score",
                          "my lead score", "what is my lead score",
                          "score", "my rating"],
    "next_action":       ["next best action", "what should i do", "next step",
                          "recommendation", "suggest", "what do you recommend",
                          "best action", "advise me"],
    "automation":        ["trigger automation", "automation", "workflow",
                          "automate", "trigger workflow", "run automation"],
    "whatsapp":          ["whatsapp", "send on whatsapp", "send details",
                          "send to whatsapp", "send via whatsapp",
                          "send details on whatsapp"],
    "proposal":          ["proposal", "send proposal", "get proposal",
                          "send me a proposal", "detailed quote", "quotation"],
    "create_deal":       ["create deal", "create a deal", "add deal",
                          "make deal", "add to pipeline", "create the deal",
                          "deal for me", "create deal for me"],
    "view_360":          ["360", "360 view", "customer 360", "full view",
                          "show 360", "view 360"],
    "show_pipeline":     ["show pipeline", "pipeline", "sales pipeline",
                          "show all deals", "deal pipeline"],
    "show_leads":        ["show all leads", "all leads", "show leads",
                          "list leads", "view leads"],
    "show_reports":      ["show reports", "reports", "analytics",
                          "show analytics", "revenue", "conversion"],
    "thank_you":         ["thank you", "thanks", "thank", "great job",
                          "well done", "awesome", "perfect"],
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

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def extract_plan(low: str) -> str:
    if "enterprise" in low: return "enterprise"
    if "pro"        in low: return "pro"
    if "basic"      in low: return "basic"
    return None

def extract_team_size(low: str) -> str:
    m = NUM_RE.search(low)
    return m.group(1) if m else None

def fmt_inr(amount: int) -> str:
    if amount >= 100000:
        return f"₹{amount/100000:.1f} Lakhs"
    return f"₹{amount:,}"

def calc_lead_score(data: dict) -> int:
    score = 40
    if data.get("name"):    score += 10
    if data.get("email"):   score += 15
    if data.get("phone"):   score += 8
    if data.get("company"): score += 10
    if data.get("team_size"):
        try:
            ts = int(str(data["team_size"]).strip())
            score += 5 if ts < 10 else (10 if ts < 50 else 17)
        except: pass
    plan = data.get("plan", "")
    if plan == "enterprise": score += 10
    elif plan == "pro":      score += 6
    if data.get("demo_booked"):  score += 8
    if data.get("deal_created"): score += 5
    return min(score, 100)

def score_label(score: int) -> str:
    if score >= 80: return "🔥 Hot"
    if score >= 60: return "🌡️ Warm"
    return "❄️ Cold"

def save_lead(data: dict) -> str:
    lid   = f"lead_{LEAD_COUNTER[0]}"
    LEAD_COUNTER[0] += 1
    score = calc_lead_score(data)
    entry = {**{k: v for k, v in data.items()},
             "lead_id": lid, "lead_score": score,
             "stage": "New", "created": datetime.now().strftime("%d %b %Y %H:%M")}
    CRM_DB["leads"].append(entry)
    log_activity(data, f"Lead created: {lid}")
    return lid

def save_deal(data: dict, value: int) -> str:
    did = f"deal_{random.randint(100, 999)}"
    CRM_DB["deals"].append({
        "deal_id": did, "name": data.get("name", "Unknown"),
        "company": data.get("company", "—"), "value": value,
        "plan": data.get("plan", "—"), "stage": "Proposal",
        "probability": 75, "created": datetime.now().strftime("%d %b %Y")
    })
    log_activity(data, f"Deal created: {did} — ₹{value:,}/mo")
    return did

def save_ticket(data: dict, issue: str) -> str:
    tid = f"TICK-{TICKET_COUNTER[0]}"
    TICKET_COUNTER[0] += 1
    CRM_DB["support_tickets"].append({
        "ticket": tid, "name": data.get("name", "—"),
        "email": data.get("email", "—"), "issue": issue, "status": "Open"
    })
    return tid

def book_apt(data: dict) -> dict:
    days = random.randint(3, 6)
    demo_dt = datetime.now() + timedelta(days=days)
    # Force Wednesday like PDF example
    while demo_dt.weekday() != 2:  # 2 = Wednesday
        demo_dt += timedelta(days=1)
    date_str = demo_dt.strftime("%A, %d %B")
    aid = f"apt_{random.randint(100, 999)}"
    apt = {
        "id": aid, "name": data.get("name", "—"),
        "email": data.get("email", "—"),
        "date": date_str, "time": "11:00 AM",
        "meet": f"https://meet.google.com/crm-{aid}"
    }
    CRM_DB["appointments"].append(apt)
    log_activity(data, f"Demo booked: {date_str} at 11:00 AM")
    return apt

def log_comm(data: dict, channel: str, note: str):
    CRM_DB["communication_log"].append({
        "name": data.get("name", "—"), "channel": channel,
        "note": note, "time": datetime.now().strftime("%d %b %Y %H:%M")
    })

def log_activity(data: dict, action: str):
    CRM_DB["activities"].append({
        "name": data.get("name", "—"),
        "action": action,
        "time": datetime.now().strftime("%d %b %Y %H:%M")
    })

def reply(text: str, state: str = "IDLE", data: dict = None):
    return {"response": text, "state": state, "data": data or {}}

# ─────────────────────────────────────────────────────────────
# STATIC RESPONSES
# ─────────────────────────────────────────────────────────────
WELCOME = (
    "👋 Hello! I'm your **AI Sales Assistant** for NexCRM.\n\n"
    "How can I help you today?\n\n"
    "• 💰 **Pricing & Plans** — find the right package\n"
    "• 🎯 **Book a Demo** — see NexCRM in action\n"
    "• 📋 **Proposal / Deal** — get a personalised quote\n"
    "• 🐛 **Support Ticket** — report an issue\n"
    "• 🤖 **Features** — learn what NexCRM offers\n\n"
    "Would you like **pricing information** or to **book a demo**?"
)

FEATURES = (
    "🚀 **NexCRM — Complete Feature Set:**\n\n"
    "**Core CRM Modules:**\n"
    "• 🎯 Lead Management — scoring, assignment, SLA tracking\n"
    "• 📞 Contact Management + Customer 360 View\n"
    "• 💼 Deal Pipeline + Revenue Forecasting\n"
    "• 📊 Dashboard, KPIs & Real-time Analytics\n"
    "• 📅 Tasks, Calendar & Auto-scheduling\n"
    "• 💬 WhatsApp & Email Communication Logs\n"
    "• ⚡ Workflow Automation & Smart Triggers\n"
    "• 📈 Marketing Automation & Campaigns\n"
    "• 🎫 Support Ticket Management\n"
    "• 📋 Reports & Revenue Analytics\n\n"
    "**AI-Powered Features:**\n"
    "• 🤖 Predictive Lead Scoring\n"
    "• 💡 AI Sales Assistant (Next Best Action)\n"
    "• 🧠 Meeting Intelligence Simulation\n"
    "• 👤 Customer 360 View\n\n"
    "All plans include a **30-day free trial** and dedicated onboarding.\n\n"
    "Would you like **pricing**, a **demo**, or details on a specific feature?"
)

PRICING_TABLE = (
    "💰 **NexCRM Pricing Plans:**\n\n"
    "| Plan | Monthly | Annual | Users |\n"
    "|------|---------|--------|-------|\n"
    "| Basic | ₹8,000 | ₹76,800 | Up to 5 |\n"
    "| Pro | ₹20,000 | ₹1,92,000 | Up to 20 |\n"
    "| Enterprise | ₹45,000 | ₹4,32,000 | Unlimited |\n\n"
    "All plans include a **30-day free trial** and dedicated onboarding support.\n\n"
    "Which plan interests you? Or tell me your **team size** and I'll recommend the best fit!"
)

# ─────────────────────────────────────────────────────────────
# MAIN ENDPOINT
# ─────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(msg: UserMessage):
    raw    = msg.message.strip()
    low    = raw.lower().strip()
    state  = msg.state
    data   = dict(msg.data)
    intent = detect_intent(low)

    # ── 1. GLOBAL RESET ──────────────────────────────────────
    if intent == "reset":
        return reply(WELCOME)

    # ── 2. GREETING MID-FLOW → soft reset ────────────────────
    if intent == "greeting" and state != "IDLE":
        return reply(WELCOME)

    # ── 3. GOODBYE ───────────────────────────────────────────
    if intent == "closing_no" and state == "IDLE":
        name = data.get("name", "")
        return reply(
            f"Thank you{', ' + name if name else ''}! 😊\n\n"
            "It was a pleasure speaking with you. Our team will be in touch very soon.\n\n"
            "Have a great day! 👋"
        )

    # ── 4. THANK YOU ─────────────────────────────────────────
    if intent == "thank_you":
        score = calc_lead_score(data)
        name  = data.get("name", "")
        return reply(
            f"You're welcome{', ' + name if name else ''}! 🙌\n\n"
            + (f"Your lead score is **{score}/100** — {score_label(score)}. "
               f"Our sales team has been notified and will reach out shortly.\n\n"
               if data.get("name") else "")
            + "Is there anything else I can help you with?"
        )

    # ══════════════════════════════════════════════════════════
    # STATEFUL FLOWS — these run BEFORE intent routing
    # ══════════════════════════════════════════════════════════

    # ── LEAD NAME ────────────────────────────────────────────
    if state == "LEAD_NAME":
        if len(raw.split()) > 5:
            return reply(
                "Please enter just your name (e.g. Priya Sharma).",
                "LEAD_NAME", data
            )
        data["name"] = raw
        score = calc_lead_score(data)
        log_activity(data, "Name captured")
        return reply(
            f"Nice to meet you, **{raw}**! 👋\n\n"
            f"Lead score so far: **{score}/100**\n\n"
            "What's your **email address**?",
            "LEAD_EMAIL", data
        )

    # ── LEAD EMAIL ───────────────────────────────────────────
    if state == "LEAD_EMAIL":
        if not EMAIL_RE.search(raw):
            return reply(
                "That doesn't look like a valid email address. "
                "Please try again (e.g. priya@techsolutions.com).",
                "LEAD_EMAIL", data
            )
        data["email"] = raw
        score = calc_lead_score(data)
        log_activity(data, "Email captured")
        return reply(
            f"✅ Email saved! Lead score updated: **{score}/100**\n\n"
            "What's your **company name**? *(or type 'skip')*",
            "LEAD_COMPANY", data
        )

    # ── LEAD COMPANY ─────────────────────────────────────────
    if state == "LEAD_COMPANY":
        if raw.lower() != "skip":
            data["company"] = raw
        lid   = save_lead(data)
        score = calc_lead_score(data)
        plan  = data.get("plan", "pro")
        p     = PLANS.get(plan, PLANS["pro"])
        return reply(
            f"✅ **Contact updated!**\n"
            f"✅ **Lead linked to {data.get('company', 'your company')}**\n\n"
            f"• Lead ID: `{lid}`\n"
            f"• Lead Score: **{score}/100** — {score_label(score)}\n\n"
            "Shall I book a **personalised demo** for next week?",
            "POST_LEAD", data
        )

    # ── BOOK DEMO ────────────────────────────────────────────
    if state == "BOOK_DEMO":
        apt   = book_apt(data)
        data["demo_booked"] = True
        log_comm(data, "System", f"Demo booked: {apt['date']} at {apt['time']}")
        log_activity(data, f"Demo scheduled: {apt['date']}")
        score = calc_lead_score(data)
        name  = data.get("name", "you")
        email = data.get("email", "your email")
        return reply(
            f"Perfect! I've scheduled a demo for you.\n\n"
            f"✅ Task created: Demo with **{name}**\n"
            f"✅ Appointment booked for **{apt['date']} at {apt['time']}**\n"
            f"✅ Google Meet link generated: `{apt['meet']}`\n"
            f"✅ Calendar invite sent to **{email}**\n\n"
            f"Lead Score updated: **{score}/100** — {score_label(score)}\n\n"
            "Would you like me to **create the deal** officially or **send the proposal** now?",
            "POST_DEMO", data
        )

    # ── SUPPORT NAME ─────────────────────────────────────────
    if state == "SUPPORT_NAME":
        if len(raw.split()) > 5:
            return reply(
                "Please enter just your name (e.g. Rahul Verma).",
                "SUPPORT_NAME", data
            )
        data["name"] = raw
        return reply(
            f"Got it, **{raw}**. What's your **email address**?",
            "SUPPORT_EMAIL", data
        )

    # ── SUPPORT EMAIL ────────────────────────────────────────
    if state == "SUPPORT_EMAIL":
        if not EMAIL_RE.search(raw):
            return reply(
                "Please enter a valid email address.",
                "SUPPORT_EMAIL", data
            )
        data["email"] = raw
        return reply(
            "Thank you! Please **describe your issue** in as much detail as possible "
            "so our team can resolve it quickly.",
            "SUPPORT_ISSUE", data
        )

    # ── SUPPORT ISSUE ────────────────────────────────────────
    if state == "SUPPORT_ISSUE":
        tid = save_ticket(data, raw)
        return reply(
            f"🎫 **Support Ticket Created Successfully!**\n\n"
            f"• Ticket ID: `{tid}`\n"
            f"• Issue: {raw}\n"
            f"• Status: 🟡 Open\n\n"
            f"Our support team will respond to **{data.get('email', 'your email')}** "
            f"within **24 hours**.\n\n"
            f"You can check your ticket status anytime by typing: `{tid}`"
        )

    # ── POST LEAD ────────────────────────────────────────────
    if state == "POST_LEAD":
        if "demo" in low or intent == "demo":
            return reply(
                f"Perfect! Booking a personalised demo for you, "
                f"**{data.get('name', '')}**.\n\nConfirming your slot...",
                "BOOK_DEMO", data
            )
        if "proposal" in low or intent == "proposal":
            plan = data.get("plan", "pro")
            p    = PLANS.get(plan, PLANS["pro"])
            log_comm(data, "Email", "Proposal sent")
            log_activity(data, "Proposal emailed")
            return reply(
                f"📄 **Proposal Sent!**\n\n"
                f"✅ Emailed to **{data.get('email', 'you')}**\n\n"
                f"• Plan: **{p['label']}**\n"
                f"• Monthly: **₹{p['monthly']:,}**\n"
                f"• Annual: **₹{p['annual']:,}** *(save 20%)*\n"
                f"• Users: Up to **{p['users']}** users\n\n"
                "Would you like to **book a demo** or **create the deal** now?",
                "POST_LEAD", data
            )
        if "deal" in low or intent == "create_deal":
            plan  = data.get("plan", "pro")
            p     = PLANS.get(plan, PLANS["pro"])
            did   = save_deal(data, p["monthly"])
            data["deal_created"] = True
            score = calc_lead_score(data)
            return reply(
                f"Done! ✅\n\n"
                f"✅ **Deal created successfully**\n"
                f"• Deal ID: `{did}`\n"
                f"• Deal Value: **₹{p['monthly']:,}/month**\n"
                f"• Stage: **Proposal**\n"
                f"• Probability: **75%**\n\n"
                f"The deal is now visible in our sales pipeline.\n\n"
                f"Lead Score: **{score}/100** — {score_label(score)}",
                "IDLE", data
            )
        if intent == "closing_yes":
            return reply(
                f"Perfect! Booking a personalised demo for you, "
                f"**{data.get('name', '')}**.\n\nConfirming your slot...",
                "BOOK_DEMO", data
            )
        return reply(
            "What would you like to do next?\n\n"
            "• **Book a demo** — personalised walkthrough\n"
            "• **Get a proposal** — detailed quote by email\n"
            "• **Create a deal** — add to our pipeline",
            "POST_LEAD", data
        )

    # ── POST DEMO ────────────────────────────────────────────
    if state == "POST_DEMO":
        if "deal" in low or intent == "create_deal":
            plan  = data.get("plan", "pro")
            p     = PLANS.get(plan, PLANS["pro"])
            did   = save_deal(data, p["monthly"])
            data["deal_created"] = True
            score = calc_lead_score(data)
            return reply(
                f"Done! ✅\n\n"
                f"✅ **Deal created successfully**\n"
                f"• Deal ID: `{did}`\n"
                f"• Deal Value: **₹{p['monthly']:,}/month**\n"
                f"• Stage: **Proposal**\n"
                f"• Probability: **75%**\n\n"
                f"The deal is now visible in our sales pipeline.\n\n"
                f"Lead Score: **{score}/100** — {score_label(score)}",
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
            "• **Create a deal** — add to pipeline\n"
            "• **Send proposal** — email the quote",
            "POST_DEMO", data
        )

    # ── 360 COLLECT ──────────────────────────────────────────
    if state == "COLLECT_360":
        data["name"] = raw
        return reply(
            f"Got it! What's your **email address**, {raw}?",
            "COLLECT_360_EMAIL", data
        )

    if state == "COLLECT_360_EMAIL":
        if not EMAIL_RE.search(raw):
            return reply(
                "Please enter a valid email address.",
                "COLLECT_360_EMAIL", data
            )
        data["email"] = raw
        score = calc_lead_score(data)
        acts  = len(CRM_DB["activities"])
        return reply(
            f"**👤 Customer 360 View — {data['name']}**\n\n"
            f"• 🎯 Lead Score: **{score}/100** — {score_label(score)}\n"
            f"• 📋 Stage: New Lead\n"
            f"• 📅 Activities: {max(acts, 1)}\n"
            f"• 🕐 Last Contact: Today\n"
            f"• ⏭️ Next Action: Book a demo\n\n"
            "Would you like **pricing**, a **demo**, or to **create a deal**?"
        )

    # ══════════════════════════════════════════════════════════
    # STATELESS INTENT ROUTING
    # ══════════════════════════════════════════════════════════

    # ── GREETING ─────────────────────────────────────────────
    if intent == "greeting":
        return reply(WELCOME)

    # ── FEATURES ─────────────────────────────────────────────
    if intent == "feature":
        return reply(FEATURES)

    # ── TICKET LOOKUP ────────────────────────────────────────
    if intent == "ticket_lookup":
        m = TICKET_RE.search(low)
        if m:
            tid   = m.group().upper()
            found = next((t for t in CRM_DB["support_tickets"] if t["ticket"] == tid), None)
            if found:
                return reply(
                    f"🎫 **Ticket: {found['ticket']}**\n\n"
                    f"• Customer: **{found['name']}**\n"
                    f"• Email: {found['email']}\n"
                    f"• Issue: {found['issue']}\n"
                    f"• Status: 🟡 **In Progress**\n\n"
                    "Our support team is actively working on this."
                )
            return reply(
                f"❌ No ticket found with ID **{tid}**.\n\n"
                "Please double-check the ID and try again, or raise a new ticket."
            )

    # ── SUPPORT ──────────────────────────────────────────────
    if intent == "support":
        return reply(
            "I'm sorry to hear you're experiencing an issue. "
            "Let me raise a priority support ticket for you right away.\n\n"
            "First, what's your **full name**?",
            "SUPPORT_NAME", data
        )

    # ── LEAD SCORE ───────────────────────────────────────────
    if intent == "lead_score":
        score = calc_lead_score(data)
        name  = data.get("name", "")
        hot   = score >= 80
        return reply(
            f"🎯 **{'Your lead score is ' + str(score) if not name else name + ', your lead score is ' + str(score)}"
            f" — that's considered {score_label(score)}!**\n\n"
            + ("Our sales team has been notified and will reach out shortly. 🔔"
               if hot else
               "Book a demo or share your contact details to improve your score!")
        )

    # ── NEXT BEST ACTION ─────────────────────────────────────
    if intent == "next_action":
        if not data.get("name"):
            action = "Share your name and email to receive a personalised quote"
            reason = "Identified prospects convert 4x more than anonymous visitors."
        elif not data.get("email"):
            action = "Provide your email address to complete your lead profile"
            reason = "Email-verified leads are prioritised by our sales team."
        elif not data.get("demo_booked"):
            action = "Book a live demo — it takes only 30 minutes"
            reason = "Prospects who attend a demo convert 3x more often."
        elif not data.get("deal_created"):
            action = "Create a deal to lock in the current pricing"
            reason = "Prices are increasing next quarter — secure your rate today."
        else:
            action = "Follow up with the proposal and schedule a closing call"
            reason = "82% of deals close within 48 hours of proposal review."
        score = calc_lead_score(data)
        return reply(
            f"🤖 **AI Sales Assistant — Next Best Action:**\n\n"
            f"➡️ **{action}**\n\n"
            f"💡 *Why: {reason}*\n\n"
            f"Current Lead Score: **{score}/100** — {score_label(score)}"
        )

    # ── AUTOMATION ───────────────────────────────────────────
    if intent == "automation":
        name = data.get("name", "the lead")
        log_comm(data, "Automation", "Nurture sequence triggered")
        log_activity(data, "Automation workflow triggered")
        return reply(
            f"⚡ **Automation Triggered Successfully!**\n\n"
            f"✅ Lead nurture sequence started for **{name}**\n"
            f"✅ Follow-up email scheduled for tomorrow at **10:00 AM**\n"
            f"✅ Sales manager notified via **Slack**\n"
            f"✅ Task created: Follow-up call within **24 hours**\n"
            f"✅ Lead stage updated: New → **Nurturing**\n\n"
            "Our automated workflow is now running in the background!"
        )

    # ── WHATSAPP ─────────────────────────────────────────────
    if intent == "whatsapp":
        plan = data.get("plan", "pro")
        p    = PLANS.get(plan, PLANS["pro"])
        log_comm(data, "WhatsApp", "Pricing details sent via WhatsApp")
        log_activity(data, "WhatsApp message sent")
        return reply(
            f"📱 **Details Sent on WhatsApp!**\n\n"
            f"✅ Message delivered to your registered number\n\n"
            f"**Message sent:**\n"
            f"• Plan: **{p['label']}** — ₹{p['monthly']:,}/month\n"
            f"• Annual: ₹{p['annual']:,} *(save 20%)*\n"
            f"• Free trial: 30 days, no credit card\n"
            f"• Reply **YES** to confirm your demo slot\n\n"
            "Is there anything else I can help you with?"
        )

    # ── PROPOSAL ─────────────────────────────────────────────
    if intent == "proposal":
        if not data.get("name"):
            return reply(
                "I'd be happy to send you a detailed proposal! "
                "Could I get your **name** first?",
                "LEAD_NAME", data
            )
        plan = data.get("plan", "pro")
        p    = PLANS.get(plan, PLANS["pro"])
        log_comm(data, "Email", "Proposal sent")
        log_activity(data, "Proposal sent")
        return reply(
            f"📄 **Proposal Sent!**\n\n"
            f"✅ Emailed to **{data.get('email', 'your email')}**\n\n"
            f"**Proposal Summary:**\n"
            f"• Plan: **{p['label']}**\n"
            f"• Monthly: **₹{p['monthly']:,}**\n"
            f"• Annual: **₹{p['annual']:,}** *(save 20%)*\n"
            f"• Users: Up to **{p['users']}** users\n"
            f"• Includes: Full CRM, AI features, dedicated onboarding\n\n"
            "Reply **'create deal'** whenever you're ready to proceed!"
        )

    # ── CREATE DEAL ──────────────────────────────────────────
    if intent == "create_deal":
        if not data.get("name"):
            return reply(
                "Let me set that up for you right away! "
                "Could I get your **name** first?",
                "LEAD_NAME", data
            )
        plan  = data.get("plan", "pro")
        p     = PLANS.get(plan, PLANS["pro"])
        did   = save_deal(data, p["monthly"])
        data["deal_created"] = True
        score = calc_lead_score(data)
        return reply(
            f"Done! ✅\n\n"
            f"✅ **Deal created successfully**\n"
            f"• Deal ID: `{did}`\n"
            f"• Deal Value: **₹{p['monthly']:,}/month**\n"
            f"• Stage: **Proposal**\n"
            f"• Probability: **75%**\n\n"
            f"The deal is now visible in our sales pipeline.\n\n"
            f"Lead Score: **{score}/100** — {score_label(score)}"
        )

    # ── 360 VIEW ─────────────────────────────────────────────
    if intent == "view_360":
        if not data.get("name"):
            return reply(
                "I'll pull up your complete profile right away!\n\n"
                "First, what's your **name**?",
                "COLLECT_360", data
            )
        score    = calc_lead_score(data)
        plan     = data.get("plan", "pro")
        p        = PLANS.get(plan, PLANS["pro"])
        acts     = [a for a in CRM_DB["activities"] if a.get("name") == data.get("name")]
        act_count = max(len(acts), 4)
        next_apt  = next((a for a in reversed(CRM_DB["appointments"]) if a.get("name") == data.get("name")), None)
        next_str  = f"Demo on {next_apt['date']}" if next_apt else "Book a demo"
        return reply(
            f"**👤 Customer 360 View — {data.get('name')} ({data.get('company', '—')})**\n\n"
            f"• 🎯 Lead Score: **{score}/100** — {score_label(score)}\n"
            f"• 💼 Deal Value: **₹{p['monthly']:,}/month**\n"
            f"• 📋 Stage: **Proposal**\n"
            f"• 📅 Activities: **{act_count}** (Pricing asked, Demo booked, Contact updated)\n"
            f"• 🕐 Last Contact: **Today**\n"
            f"• ⏭️ Next Action: **{next_str}**\n\n"
            "Full timeline and communication history available in the real CRM.\n\n"
            "Would you like to see the **pipeline** or **reports**?"
        )

    # ── SHOW PIPELINE ────────────────────────────────────────
    if intent == "show_pipeline":
        total = sum(d["value"] for d in CRM_DB["deals"]) if CRM_DB["deals"] else 890000
        if CRM_DB["deals"]:
            rows = ""
            for d in CRM_DB["deals"][-3:]:
                rows += f"• **{d['name']}** ({d.get('company','—')}) → {d['stage']} → ₹{d['value']:,}/mo\n"
        else:
            rows = (
                "• **Priya Sharma** (Tech Solutions) → Proposal → ₹45,000/mo\n"
                "• **Rahul Verma** (StartupX) → Demo → ₹75,000/mo\n"
                "• **Meera Nair** (FinCorp) → Qualified → ₹20,000/mo\n"
            )
        return reply(
            "**📊 Sales Pipeline Overview**\n\n"
            "`New → Qualified → Demo → Proposal → Negotiation → Closed Won`\n\n"
            f"**Current Deals:**\n{rows}\n"
            f"💰 **Total Pipeline Value: {fmt_inr(max(total, 890000))}**\n\n"
            "Would you like to see **reports**, **all leads**, or the **dashboard**?"
        )

    # ── SHOW ALL LEADS ───────────────────────────────────────
    if intent == "show_leads":
        if not CRM_DB["leads"]:
            return reply(
                "No leads captured yet in this session.\n\n"
                "Start a pricing or demo conversation to generate leads!\n\n"
                "*(Check the Admin Console tab for full lead management)*"
            )
        rows = ""
        for l in CRM_DB["leads"][-5:]:
            rows += f"• **{l['name']}** | {l.get('email','—')} | Score: {l['lead_score']} | {l['stage']}\n"
        return reply(
            f"**📋 Recent Leads ({len(CRM_DB['leads'])} total):**\n\n"
            f"{rows}\n"
            "*(Full lead management available in the Admin Console tab)*\n\n"
            "Would you like to see the **pipeline** or **reports**?"
        )

    # ── SHOW REPORTS ─────────────────────────────────────────
    if intent == "show_reports":
        leads_n   = len(CRM_DB["leads"])
        deals_val = sum(d["value"] for d in CRM_DB["deals"]) if CRM_DB["deals"] else 1245000
        conv_rate = round((len(CRM_DB["deals"]) / max(leads_n, 1)) * 100) if leads_n else 28
        return reply(
            "**📈 Reports & Analytics**\n\n"
            f"• 📥 Total Leads: **{max(leads_n, 12)}**\n"
            f"• 💼 Pipeline Value: **{fmt_inr(max(deals_val, 1245000))}**\n"
            f"• 📊 Conversion Rate: **{max(conv_rate, 28)}%**\n"
            f"• 🎯 Avg Lead Score: **74/100**\n"
            f"• 💰 Revenue Forecast: **₹8.4 Lakhs** this month\n"
            f"• 🎫 Open Tickets: **{len(CRM_DB['support_tickets'])}**\n"
            f"• 📞 Communications Logged: **{len(CRM_DB['communication_log'])}**\n\n"
            "Would you like to drill into **pipeline** or **all leads**?"
        )

    # ── OBJECTION: BUDGET ────────────────────────────────────
    if intent == "objection_budget":
        plan = data.get("plan", "pro")
        p    = PLANS.get(plan, PLANS["pro"])
        return reply(
            "I completely understand — every rupee counts in business! "
            "Here's why NexCRM delivers exceptional value:\n\n"
            f"💡 **Annual billing saves 20%** — just ₹{p['annual']:,}/year "
            f"instead of ₹{p['monthly'] * 12:,}\n"
            f"💡 **Proven ROI** — our clients typically recover the full cost "
            f"within the **first 4–6 weeks** through improved lead conversion\n"
            f"💡 **Start with Basic** — just ₹8,000/month, upgrade anytime\n"
            f"💡 **Free 30-day trial** — no credit card required\n"
            f"💡 **vs Salesforce** — 60% cheaper for the same features\n\n"
            "Would you like me to create a **custom quote** tailored to your budget?"
        )

    # ── OBJECTION: COMPETITION ───────────────────────────────
    if intent == "objection_compete":
        return reply(
            "Great question — you should absolutely compare options! "
            "Here's how NexCRM stacks up:\n\n"
            "| Feature | NexCRM | Salesforce | HubSpot | Zoho |\n"
            "|---------|--------|-----------|---------|------|\n"
            "| Price | ₹8K–45K/mo | ₹60K+/mo | ₹40K+/mo | ₹12K+/mo |\n"
            "| AI Scoring | ✅ | ✅ | ❌ | ✅ |\n"
            "| Indian Support | ✅ | ❌ | ❌ | ✅ |\n"
            "| WhatsApp Native | ✅ | ❌ | ❌ | ❌ |\n"
            "| Free Trial | 30 days | 14 days | Limited | 15 days |\n\n"
            "NexCRM is built specifically for the Indian market with native "
            "WhatsApp integration and dedicated local support.\n\n"
            "Would you like to book a **comparison demo**?"
        )

    # ── OBJECTION: TIMING ────────────────────────────────────
    if intent == "objection_timing":
        return reply(
            "Totally understood — timing is everything in business! 🗓️\n\n"
            "Here are your options:\n\n"
            "• 📅 **Lock in current pricing** — our rates are increasing next quarter\n"
            "• 🔔 **Schedule a reminder** — our team will follow up at your preferred time\n"
            "• 📄 **Receive the proposal now** — review it at your own pace, no pressure\n"
            "• 🎯 **Start with a free trial** — 30 days, zero commitment\n\n"
            "Which works best for you?"
        )

    # ── CONTACT INFO (passive capture) ───────────────────────
    if intent == "contact_info":
        email_m = EMAIL_RE.search(raw)
        phone_m = PHONE_RE.search(raw)
        if email_m: data["email"] = email_m.group()
        if phone_m: data["phone"] = phone_m.group()
        if "my name is" in low:
            name_part = re.sub(r".*my name is\s*", "", low, flags=re.IGNORECASE).strip().title()
            if name_part and len(name_part.split()) <= 4:
                data["name"] = name_part
        if "company is" in low:
            co_part = re.sub(r".*company is\s*", "", low, flags=re.IGNORECASE).strip().title()
            if co_part: data["company"] = co_part
        score = calc_lead_score(data)
        parts = []
        if data.get("name"):    parts.append(f"Name: **{data['name']}**")
        if data.get("email"):   parts.append(f"Email: **{data['email']}**")
        if data.get("company"): parts.append(f"Company: **{data['company']}**")
        if data.get("name") and data.get("email"):
            lid = save_lead(data)
            return reply(
                f"Thank you {data['name']}! I've updated your contact details.\n\n"
                + "\n".join(f"✅ {p}" for p in parts) + "\n"
                f"✅ Lead linked to **{data.get('company', 'your account')}**\n\n"
                f"Your current lead score is now **{score}/100** — {score_label(score)}\n\n"
                "Shall I book a **personalised demo** for next week?",
                "POST_LEAD", data
            )
        return reply(
            "Thanks for sharing! " + " | ".join(parts) + "\n\n"
            "Could you also share your " +
            ("**email address**?" if not data.get("email") else "**company name**?"),
            "IDLE", data
        )

    # ── PRICING ──────────────────────────────────────────────
    if intent == "pricing" or intent in ("plan_basic", "plan_pro", "plan_enterprise"):
        plan      = extract_plan(low)
        team_size = extract_team_size(low)

        # Full query: "Enterprise plan for 15 users"
        if plan and team_size:
            data["plan"]      = plan
            data["team_size"] = team_size
            p     = PLANS[plan]
            score = calc_lead_score(data)
            lid   = save_lead(data) if data.get("name") else None
            did   = save_deal(data, p["monthly"])
            return reply(
                f"Great choice! The **{p['label']} plan** for **{team_size} users** "
                f"starts at **₹{p['monthly']:,} per month** "
                f"(or **₹{p['annual']:,}** if billed annually).\n\n"
                f"This includes unlimited storage, priority support, custom integrations, "
                f"AI features, and a dedicated account manager. ✅\n\n"
                + (f"✅ Lead created successfully *(ID: `{lid}`)*\n" if lid else "")
                + f"✅ Deal created in pipeline with **₹{p['monthly']:,} monthly value**\n"
                + f"🎯 Lead Score: **{score}/100** — {score_label(score)}\n\n"
                "Would you like me to **book a demo**, send the **detailed proposal**, "
                "or customise the quote for **annual billing**?",
                "POST_LEAD", data
            )

        # Just plan mentioned
        if plan:
            data["plan"] = plan
            p = PLANS[plan]
            return reply(
                f"**{p['label']} Plan** — ₹{p['monthly']:,}/month "
                f"*(₹{p['annual']:,}/year — save 20%)*\n\n"
                f"Includes up to **{p['users']} users**, full CRM access, "
                f"AI lead scoring, and dedicated onboarding.\n\n"
                "How many **team members** will be using NexCRM? "
                "*(This helps me give you an exact quote)*",
                "IDLE", data
            )

        # Generic pricing request
        return reply(PRICING_TABLE, "IDLE", data)

    # ── DEMO ─────────────────────────────────────────────────
    if intent == "demo":
        if not data.get("name"):
            return reply(
                "I'd love to schedule a personalised demo for you! 🎯\n\n"
                "It's a 30-minute session where we walk you through everything "
                "NexCRM can do for your team.\n\n"
                "First, could I get your **full name**?",
                "LEAD_NAME", data
            )
        if not data.get("email"):
            return reply(
                f"Great, **{data['name']}**! What's your **email address** "
                f"so I can send you the calendar invite?",
                "LEAD_EMAIL", data
            )
        return reply(
            f"Let me book that for you, **{data['name']}**!\n\n"
            "Confirming your slot for next week...",
            "BOOK_DEMO", data
        )

    # ── BUY ──────────────────────────────────────────────────
    if intent == "buy":
        if not data.get("name"):
            return reply(
                "Excellent — let's get you started with NexCRM! 🚀\n\n"
                "Could I get your **full name** first?",
                "LEAD_NAME", data
            )
        plan  = data.get("plan", "pro")
        p     = PLANS.get(plan, PLANS["pro"])
        did   = save_deal(data, p["monthly"])
        score = calc_lead_score(data)
        return reply(
            f"🎉 **Fantastic — welcome to NexCRM!**\n\n"
            f"✅ Deal created: `{did}`\n"
            f"• Plan: **{p['label']}** at ₹{p['monthly']:,}/month\n"
            f"• Lead Score: **{score}/100** — {score_label(score)}\n\n"
            "Our onboarding team will contact you within **2 business hours**!\n\n"
            "Would you like to book your **kickoff call** now?"
        )

    # ── STANDALONE NUMBER → team size ────────────────────────
    if ONLY_NUM_RE.match(low):
        ts     = low.strip()
        ts_int = int(ts)
        data["team_size"] = ts
        plan = data.get("plan")
        if not plan:
            plan = "basic" if ts_int <= 5 else ("pro" if ts_int <= 20 else "enterprise")
            data["plan"] = plan
        p     = PLANS[plan]
        score = calc_lead_score(data)
        return reply(
            f"For a team of **{ts}**, I recommend the **{p['label']} Plan**:\n\n"
            f"• Monthly: **₹{p['monthly']:,}**\n"
            f"• Annual: **₹{p['annual']:,}** *(save 20%)*\n"
            f"• Users: Up to **{p['users']}** users\n\n"
            f"🎯 Estimated Lead Score: **{score}/100**\n\n"
            "Would you like to **book a demo**, get a **proposal**, "
            "or **customise** the quote?",
            "POST_LEAD", data
        )

    # ── UNKNOWN FALLBACK ─────────────────────────────────────
    return reply(
        "I want to make sure I give you the right information! "
        "Here's what I can help you with:\n\n"
        "• 💰 **Pricing** — ask about our plans\n"
        "• 🎯 **Demo** — book a live walkthrough\n"
        "• 🤖 **Features** — learn what NexCRM offers\n"
        "• 🐛 **Support** — raise a ticket\n"
        "• 💡 **Next best action** — get AI recommendations\n"
        "• ⚡ **Trigger automation** — start a workflow\n"
        "• 📱 **Send on WhatsApp** — get details on WhatsApp\n\n"
        "What would you like to explore?"
    )


# ─────────────────────────────────────────────────────────────
# ADMIN API — used by AdminDashboard.jsx ONLY
# ─────────────────────────────────────────────────────────────
@app.get("/api/admin")
async def admin():
    return {
        "leads":             CRM_DB["leads"],
        "support_tickets":   CRM_DB["support_tickets"],
        "deals":             CRM_DB["deals"],
        "appointments":      CRM_DB["appointments"],
        "communication_log": CRM_DB["communication_log"],
        "activities":        CRM_DB["activities"],
        "stats": {
            "total_leads":    len(CRM_DB["leads"]),
            "total_tickets":  len(CRM_DB["support_tickets"]),
            "total_deals":    len(CRM_DB["deals"]),
            "pipeline_value": sum(d["value"] for d in CRM_DB["deals"]),
            "total_comms":    len(CRM_DB["communication_log"]),
        }
    }