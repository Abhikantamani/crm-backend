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
    "leads": [],
    "contacts": [],
    "deals": [],
    "tasks": [],
    "appointments": [],
    "communication_log": [],
    "support_tickets": [],
}
LEAD_COUNTER = [784]

# ── Pricing ───────────────────────────────────────────────────
PLANS = {
    "basic":      {"monthly": 8000,   "annual": 76800,   "users": 5,   "label": "Basic"},
    "pro":        {"monthly": 20000,  "annual": 192000,  "users": 20,  "label": "Pro"},
    "enterprise": {"monthly": 45000,  "annual": 432000,  "users": 999, "label": "Enterprise"},
}

# ── Regex ─────────────────────────────────────────────────────
EMAIL_RE    = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE    = re.compile(r"[\+]?[\d][\d\s\-]{8,14}\d")
TICK_RE     = re.compile(r"tick-\d+", re.IGNORECASE)
NUM_RE      = re.compile(r"\b(\d+)\b")
ONLY_NUM_RE = re.compile(r"^\d+$")

# ── Intent keywords ───────────────────────────────────────────
# greeting and reset use WHOLE-WORD matching to avoid "hi" in "abhiram"
INTENT_MAP = {
    "greeting":          ["hi", "hello", "hey", "good morning", "good evening", "namaste", "start"],
    "reset":             ["cancel", "start over", "restart", "reset", "menu", "main menu"],
    "pricing":           ["price", "pricing", "cost", "plan", "plans", "package", "how much", "rate", "fees", "charge"],
    "demo":              ["demo", "demonstration", "walkthrough", "show me", "trial", "book a demo", "schedule demo"],
    "buy":               ["buy", "purchase", "subscribe", "sign up", "get started", "i want to buy"],
    "feature":           ["feature", "features", "what can", "capability", "capabilities", "include", "offer"],
    "support":           ["bug", "error", "broken", "issue", "problem", "not working", "support", "login", "password", "raise a ticket", "support ticket", "got a bug", "i got a bug"],
    "ticket_lookup":     ["tick-"],
    "objection_budget":  ["expensive", "costly", "too much", "high price", "cheaper", "discount"],
    "objection_compete": ["competitor", "salesforce", "hubspot", "zoho", "freshsales", "other crm"],
    "objection_timing":  ["not now", "later", "next month", "next quarter", "not ready"],
    "closing_yes":       ["yes", "sure", "okay", "ok", "proceed", "go ahead", "confirm", "let's do"],
    "closing_no":        ["nope", "not interested", "maybe later", "goodbye", "exit"],
    "admin_dashboard":   ["show dashboard", "admin mode", "admin", "dashboard", "show all leads", "view 360", "show pipeline", "show reports", "pipeline", "all leads", "reports", "analytics"],
    "lead_score":        ["lead score", "my score", "what is my score"],
    "next_action":       ["next best action", "what should", "next step", "recommendation"],
    "automation":        ["trigger automation", "automation", "workflow"],
    "whatsapp":          ["whatsapp", "send on whatsapp", "send details"],
    "proposal":          ["proposal", "send proposal", "get proposal"],
    "create_deal":       ["create deal", "create a deal", "add deal", "make deal"],
    "360_view":          ["360", "360 view", "customer 360", "full view"],
    "thank_you":         ["thank you", "thanks", "thank"],
    "contact_info":      ["my name is", "email is", "phone is", "company is"],
}

# ── Intent detector with whole-word matching for safe intents ─
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
    if amount >= 100000:
        return f"₹{amount/100000:.1f} Lakhs"
    return f"₹{amount:,}"

def calc_lead_score(data: dict) -> int:
    score = 40
    if data.get("name"):        score += 10
    if data.get("email"):       score += 15
    if data.get("phone"):       score += 8
    if data.get("company"):     score += 10
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
    lid = f"lead_{LEAD_COUNTER[0]}"
    LEAD_COUNTER[0] += 1
    score = calc_lead_score(data)
    entry = {**data, "lead_id": lid, "lead_score": score,
             "stage": "New", "created": datetime.now().strftime("%d %b %Y %H:%M")}
    CRM_DB["leads"].append(entry)
    return lid

def save_deal(data: dict, value: int) -> str:
    did = f"deal_{random.randint(100,999)}"
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
    aid = f"apt_{random.randint(100,999)}"
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
    "• 💰 Pricing & Plans\n"
    "• 🎯 Book a Demo\n"
    "• 📋 Create a Deal or Proposal\n"
    "• 🐛 Raise a Support Ticket\n"
    "• 📊 View Dashboard & Pipeline *(say 'show dashboard')*\n\n"
    "What can I help you with today?"
)

FEATURES = (
    "🚀 **NexCRM Features:**\n\n"
    "• 🎯 Lead Management & Scoring\n"
    "• 📞 Contact Management & Customer 360\n"
    "• 💼 Deal / Sales Pipeline & Forecasting\n"
    "• 📊 Dashboard, KPIs & Reports\n"
    "• 📅 Tasks, Calendar & Appointments\n"
    "• 💬 WhatsApp & Email Communication\n"
    "• ⚡ Automation & Workflows\n"
    "• 🤖 Predictive Lead Scoring\n"
    "• 📈 Marketing Automation\n"
    "• 🎫 Support Ticket Management\n\n"
    "Which feature would you like to know more about?"
)

# ═══════════════════════════════════════════════════════════════
# MAIN ENDPOINT
# ═══════════════════════════════════════════════════════════════
@app.post("/chat")
async def chat(msg: UserMessage):
    raw   = msg.message.strip()
    low   = raw.lower()
    state = msg.state
    data  = dict(msg.data)

    intent = detect_intent(low)

    # ── Global reset (whole-word "cancel", "reset" etc.) ──────
    if intent == "reset":
        return reply(WELCOME)

    # ── Greeting mid-flow → reset ─────────────────────────────
    if intent == "greeting" and state != "IDLE":
        return reply(WELCOME)

    # ── Goodbye ───────────────────────────────────────────────
    if intent == "closing_no" and state == "IDLE":
        name  = data.get("name", "")
        score = calc_lead_score(data)
        return reply(
            f"Thank you{' ' + name if name else ''}! 😊\n\n"
            "It was great chatting with you. Our team will be in touch soon.\n\n"
            "Feel free to come back anytime! 👋"
        )

    # ── Thank you ─────────────────────────────────────────────
    if intent == "thank_you":
        score = calc_lead_score(data)
        return reply(
            f"You're welcome! 🙌\n\n"
            + (f"Your lead score: **{score}/100** — {score_label(score)}. Our sales team has been notified.\n\n" if data.get("name") else "")
            + "Is there anything else I can help you with?"
        )

    # ══════════════════════════════════════════════════════════
    # ADMIN / DASHBOARD MODE
    # ══════════════════════════════════════════════════════════
    if intent == "admin_dashboard" or state == "ADMIN":

        if "360" in low:
            if not data.get("name"):
                return reply("Please share your name first so I can pull your 360 view.", "COLLECT_360", data)
            score    = calc_lead_score(data)
            plan     = data.get("plan", "pro")
            p        = PLANS.get(plan, PLANS["pro"])
            deal_val = fmt_inr(p["monthly"])
            return reply(
                f"**Customer 360 View — {data.get('name')} ({data.get('company', '—')})**\n\n"
                f"• 🎯 Lead Score: **{score}/100** — {score_label(score)}\n"
                f"• 💼 Deal Value: **{deal_val}/month**\n"
                f"• 📋 Stage: **Proposal**\n"
                f"• 📅 Activities: Pricing asked, Demo booked, Contact updated\n"
                f"• 🕐 Last Contact: Today\n"
                f"• ⏭️ Next Action: Demo scheduled\n\n"
                "Would you like to see the **pipeline**, **reports**, or **all leads**?",
                "ADMIN", data
            )

        if "pipeline" in low:
            total = sum(d["value"] for d in CRM_DB["deals"]) if CRM_DB["deals"] else 890000
            if CRM_DB["deals"]:
                rows = "".join(f"• **{d['name']}** ({d.get('company','—')}) → {d['stage']} → ₹{d['value']:,}/mo\n" for d in CRM_DB["deals"][-3:])
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
                f"💰 **Total Pipeline Value: {fmt_inr(total)}**\n\n"
                "Would you like **reports**, **all leads**, or back to **dashboard**?",
                "ADMIN", data
            )

        if "all leads" in low or "show leads" in low:
            if not CRM_DB["leads"]:
                return reply("No leads captured yet. Start a conversation in the chatbot to generate leads!", "ADMIN", data)
            rows = "".join(f"• **{l['name']}** | {l.get('email','—')} | Score: {l['lead_score']} | {l['stage']}\n" for l in CRM_DB["leads"][-5:])
            return reply(f"**📋 Recent Leads ({len(CRM_DB['leads'])} total):**\n\n{rows}\nWould you like **pipeline** or **reports**?", "ADMIN", data)

        if "report" in low or "analytic" in low:
            leads_today = len(CRM_DB["leads"])
            deals_val   = sum(d["value"] for d in CRM_DB["deals"]) if CRM_DB["deals"] else 1245000
            conv_rate   = round((len(CRM_DB["deals"]) / max(len(CRM_DB["leads"]), 1)) * 100) if CRM_DB["leads"] else 28
            return reply(
                "**📈 Reports & Analytics**\n\n"
                f"• 📥 Total Leads: **{max(leads_today, 12)}**\n"
                f"• 💼 Pipeline Value: **{fmt_inr(max(deals_val, 1245000))}**\n"
                f"• 📊 Conversion Rate: **{max(conv_rate, 28)}%**\n"
                f"• 🎯 Avg Lead Score: **74/100**\n"
                f"• 💰 Revenue Forecast: **₹8.4 Lakhs** this month\n"
                f"• 🎫 Open Tickets: **{len(CRM_DB['support_tickets'])}**\n\n"
                "Would you like to drill into **pipeline** or **leads**?",
                "ADMIN", data
            )

        # Default dashboard
        leads_today = len(CRM_DB["leads"])
        deals_val   = sum(d["value"] for d in CRM_DB["deals"]) if CRM_DB["deals"] else 1245000
        return reply(
            "**📊 Admin Dashboard — Today's Summary**\n\n"
            f"• 📥 New Leads: **{max(leads_today, 3)}**\n"
            f"• 💼 Deals in Pipeline: **{fmt_inr(max(deals_val, 1245000))}**\n"
            f"• 📊 Conversion Rate: **28%**\n"
            f"• 💬 Active Conversations: **8**\n\n"
            "**Quick KPIs:**\n"
            f"• Leads Today: **{max(leads_today, 12)}**\n"
            f"• Revenue Forecast: **₹8.4 Lakhs** this month\n"
            f"• Open Tickets: **{len(CRM_DB['support_tickets'])}**\n\n"
            "Would you like to see **all leads**, **pipeline**, **360 view**, or **reports**?",
            "ADMIN", data
        )

    # ══════════════════════════════════════════════════════════
    # STATEFUL FLOWS
    # ══════════════════════════════════════════════════════════

    if state == "COLLECT_360":
        data["name"] = raw
        return reply(f"Got it! What's your **email**, {raw}?", "COLLECT_360_EMAIL", data)

    if state == "COLLECT_360_EMAIL":
        if not EMAIL_RE.search(raw):
            return reply("Please enter a valid email address.", "COLLECT_360_EMAIL", data)
        data["email"] = raw
        score = calc_lead_score(data)
        return reply(
            f"**Customer 360 View — {data['name']}**\n\n"
            f"• 🎯 Lead Score: **{score}/100** — {score_label(score)}\n"
            f"• 📋 Stage: New Lead\n"
            f"• 🕐 Last Contact: Today\n\n"
            "Would you like **pricing**, **demo**, or to **create a deal**?"
        )

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

    if state == "LEAD_EMAIL":
        if not EMAIL_RE.search(raw):
            return reply("That doesn't look valid. Please enter a proper email (e.g. priya@techsolutions.com).", "LEAD_EMAIL", data)
        data["email"] = raw
        score = calc_lead_score(data)
        return reply(
            f"✅ Email saved! Lead score: **{score}/100**\n\n"
            "What's your **company name**? *(or type 'skip')*",
            "LEAD_COMPANY", data
        )

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
            "Shall I book a **personalised demo** for next week, or would you like a **proposal**?",
            "POST_LEAD", data
        )

    if state == "BOOK_DEMO":
        apt   = book_appointment(data)
        data["demo_booked"] = True
        log_comm(data, "System", f"Demo booked for {apt['date']}")
        score = calc_lead_score(data)
        return reply(
            f"🎉 **Demo Scheduled!**\n\n"
            f"✅ Task created: Demo with **{data.get('name', 'you')}**\n"
            f"✅ Appointment: **{apt['date']} at {apt['time']}**\n"
            f"✅ Google Meet: `{apt['meet']}`\n"
            f"✅ Invite sent to **{data.get('email', 'your email')}**\n\n"
            f"Lead Score updated: **{score}/100** — {score_label(score)}\n\n"
            "Would you like me to **create the deal** or **send the proposal** now?",
            "POST_DEMO", data
        )

    if state == "SUPPORT_NAME":
        if len(raw.split()) > 4:
            return reply("Please enter just your name.", "SUPPORT_NAME", data)
        data["name"] = raw
        return reply(f"Got it, **{raw}**. What's your **email address**?", "SUPPORT_EMAIL", data)

    if state == "SUPPORT_EMAIL":
        if not EMAIL_RE.search(raw):
            return reply("Please enter a valid email.", "SUPPORT_EMAIL", data)
        data["email"] = raw
        return reply("Please **describe your issue** in detail.", "SUPPORT_ISSUE", data)

    if state == "SUPPORT_ISSUE":
        tid = save_ticket(data, raw)
        return reply(
            f"🎫 **Support Ticket Created!**\n\n"
            f"• Ticket ID: `{tid}`\n"
            f"• Issue: {raw}\n"
            f"• Status: 🟡 Open\n\n"
            f"Our support team will respond to **{data.get('email', 'your email')}** within 24 hours.\n\n"
            f"Check status anytime by typing: `{tid}`"
        )

    if state == "POST_LEAD":
        if intent in ("demo", "closing_yes") or "demo" in low:
            return reply(
                f"Perfect! Booking a demo for you, **{data.get('name', '')}**.\n\nConfirming your slot...",
                "BOOK_DEMO", data
            )
        if intent == "proposal" or "proposal" in low:
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
        if intent == "create_deal" or "deal" in low:
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
                "Type **'show pipeline'** to see it!"
            )
        return reply(
            "What would you like to do next?\n\n"
            "• **book demo** — schedule a walkthrough\n"
            "• **proposal** — receive a detailed quote\n"
            "• **create deal** — add to pipeline\n"
            "• **show dashboard** — admin view",
            "POST_LEAD", data
        )

    if state == "POST_DEMO":
        if intent == "create_deal" or "deal" in low:
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
                "Type **'show pipeline'** to see it!",
                "IDLE", data
            )
        if intent == "proposal" or "proposal" in low:
            log_comm(data, "Email", "Proposal sent")
            plan = data.get("plan", "pro")
            p    = PLANS.get(plan, PLANS["pro"])
            return reply(
                f"📄 **Proposal Sent to {data.get('email', 'you')}!**\n\n"
                f"• Plan: **{p['label']}**\n"
                f"• Monthly: **₹{p['monthly']:,}**\n"
                f"• Annual: **₹{p['annual']:,}** *(2 months free)*\n\n"
                "Type **'create deal'** when ready to proceed!",
                "POST_DEMO", data
            )
        return reply(
            "Would you like to:\n"
            "• **Create a deal** — add to pipeline\n"
            "• **Send proposal** — email the quote\n"
            "• **Show dashboard** — admin view",
            "POST_DEMO", data
        )

    # ══════════════════════════════════════════════════════════
    # STATELESS INTENT ROUTING
    # ══════════════════════════════════════════════════════════

    if intent == "greeting":
        return reply(WELCOME)

    if intent == "feature":
        return reply(FEATURES)

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
            return reply(f"❌ No ticket found with ID **{tid}**. Please check and try again.")

    if intent == "support":
        return reply(
            "I'm sorry to hear you're having trouble. Let me create a support ticket for you.\n\n"
            "First, what's your **full name**?",
            "SUPPORT_NAME", data
        )

    if intent == "lead_score":
        score = calc_lead_score(data)
        return reply(
            f"🎯 **Your Lead Score: {score}/100** — {score_label(score)}\n\n"
            + ("Our sales team has been notified and will reach out soon!" if score >= 70
               else "Book a demo or share more details to improve your score!")
        )

    if intent == "next_action":
        if not data.get("name"):
            action = "Share your name and email to get a personalised quote"
        elif not data.get("demo_booked"):
            action = "Book a demo — prospects who attend demos convert 3x more"
        elif not data.get("deal_created"):
            action = "Create a deal to lock in the pricing and move to proposal stage"
        else:
            action = "Follow up with the proposal and schedule a closing call"
        return reply(f"🤖 **AI Recommendation — Next Best Action:**\n\n➡️ **{action}**")

    if intent == "whatsapp":
        log_comm(data, "WhatsApp", "Details sent via WhatsApp")
        plan = data.get("plan", "pro")
        p    = PLANS.get(plan, PLANS["pro"])
        return reply(
            f"📱 **Details sent on WhatsApp!**\n\n"
            f"✅ Message delivered to your registered number\n\n"
            f"• Plan: {p['label']} — ₹{p['monthly']:,}/month\n"
            f"• Reply YES to book demo\n\n"
            "Is there anything else I can help you with?"
        )

    if intent == "automation":
        return reply(
            "⚡ **Automation Triggered!**\n\n"
            "✅ Lead nurture sequence started\n"
            "✅ Follow-up email scheduled for tomorrow 10:00 AM\n"
            "✅ Sales manager notified via Slack\n"
            "✅ Task created: Call back within 24 hours\n\n"
            "Our automated workflow is now running in the background!"
        )

    if intent == "proposal":
        if not data.get("name"):
            return reply("I'd be happy to send you a proposal! Could I get your **name** first?", "LEAD_NAME", data)
        plan = data.get("plan", "pro")
        p    = PLANS.get(plan, PLANS["pro"])
        log_comm(data, "Email", "Proposal sent")
        return reply(
            f"📄 **Proposal Sent!**\n\n"
            f"✅ Emailed to **{data.get('email', 'your email')}**\n\n"
            f"• Plan: **{p['label']}** — ₹{p['monthly']:,}/month\n"
            f"• Annual: ₹{p['annual']:,} *(save 20%)*\n\n"
            "Reply **'create deal'** when ready to proceed!"
        )

    if intent == "create_deal":
        if not data.get("name"):
            return reply("Let me set that up! What's your **name** first?", "LEAD_NAME", data)
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
            "Type **'show pipeline'** to see it!"
        )

    if intent == "objection_budget":
        plan = data.get("plan", "pro")
        p    = PLANS.get(plan, PLANS["pro"])
        return reply(
            "I completely understand budget concerns! Here's how we make it work:\n\n"
            f"💡 **Annual billing saves 20%** — ₹{p['annual']:,}/year\n"
            f"💡 **ROI**: Most clients recover costs in the first month\n"
            f"💡 **Start small**: Basic plan at just ₹8,000/month, upgrade anytime\n\n"
            "Would you like a **custom quote** or to speak with our team?"
        )

    if intent == "objection_compete":
        return reply(
            "Great question! Here's how NexCRM compares:\n\n"
            "• **vs Salesforce** — 60% lower cost, same enterprise features\n"
            "• **vs HubSpot** — No per-user pricing trap, unlimited contacts\n"
            "• **vs Zoho** — Better AI scoring, dedicated Indian support\n\n"
            "Plus a **free 30-day trial** with full features.\n\n"
            "Would you like to book a comparison demo?"
        )

    if intent == "objection_timing":
        return reply(
            "Totally understand — timing is everything! 🗓️\n\n"
            "• 📅 **Lock in today's pricing** — rates go up next quarter\n"
            "• 🎯 **Schedule for next month** — we'll send a reminder\n"
            "• 📄 **Send the proposal** — review at your own pace\n\n"
            "What works best for you?"
        )

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
                "How many **team members** will use NexCRM?",
                "IDLE", data
            )

        return reply(
            "💰 **NexCRM Pricing Plans:**\n\n"
            "| Plan | Monthly | Annual | Users |\n"
            "|------|---------|--------|-------|\n"
            "| Basic | ₹8,000 | ₹76,800 | Up to 5 |\n"
            "| Pro | ₹20,000 | ₹1,92,000 | Up to 20 |\n"
            "| Enterprise | ₹45,000 | ₹4,32,000 | Unlimited |\n\n"
            "All plans include a **30-day free trial**.\n\n"
            "Which plan interests you? Or tell me your **team size** and I'll recommend one!",
            "IDLE", data
        )

    if intent == "demo":
        if not data.get("name"):
            return reply("I'd love to schedule a demo! First, could I get your **name**?", "LEAD_NAME", data)
        return reply(
            f"Let me book that for you, **{data['name']}**! Confirming your slot...",
            "BOOK_DEMO", data
        )

    if intent == "buy":
        if not data.get("name"):
            return reply("Excellent! Let's get you started! 🚀\n\nFirst, could I get your **name**?", "LEAD_NAME", data)
        plan  = data.get("plan", "pro")
        p     = PLANS.get(plan, PLANS["pro"])
        did   = save_deal(data, p["monthly"])
        score = calc_lead_score(data)
        return reply(
            f"🎉 **Let's get started!**\n\n"
            f"✅ Deal created: `{did}`\n"
            f"• Plan: **{p['label']}** at ₹{p['monthly']:,}/month\n"
            f"• Lead Score: **{score}/100** — {score_label(score)}\n\n"
            "Our onboarding team will contact you within 2 hours!\n\n"
            "Would you like to book your **kickoff call** now?"
        )

    # ── Catch standalone number as team size ──────────────────
    if ONLY_NUM_RE.match(low.strip()):
        ts   = low.strip()
        data["team_size"] = ts
        plan = data.get("plan")
        if plan:
            p     = PLANS[plan]
            score = calc_lead_score(data)
            return reply(
                f"Great! For a team of **{ts}**, the **{p['label']} plan** is:\n\n"
                f"• Monthly: **₹{p['monthly']:,}**\n"
                f"• Annual: **₹{p['annual']:,}** *(save 20%)*\n\n"
                f"🎯 Lead Score: **{score}/100**\n\n"
                "Would you like to **book a demo** or get a **proposal**?",
                "POST_LEAD", data
            )
        # No plan selected yet — recommend based on size
        ts_int = int(ts)
        if ts_int <= 5:
            rec = "Basic"
        elif ts_int <= 20:
            rec = "Pro"
        else:
            rec = "Enterprise"
        p = PLANS[rec.lower()]
        data["plan"] = rec.lower()
        return reply(
            f"For a team of **{ts}**, I recommend the **{rec} Plan**:\n\n"
            f"• Monthly: **₹{p['monthly']:,}**\n"
            f"• Annual: **₹{p['annual']:,}** *(save 20%)*\n"
            f"• Users: Up to **{p['users']}** users\n\n"
            "Would you like to **book a demo**, get a **proposal**, or **customise** the quote?",
            "POST_LEAD", data
        )

    # ── Unknown fallback ──────────────────────────────────────
    return reply(
        "I didn't quite catch that. Here's what I can help with:\n\n"
        "• **Pricing** — ask about our plans\n"
        "• **Demo** — book a live walkthrough\n"
        "• **Support** — raise a ticket\n"
        "• **Dashboard** — say 'show dashboard'\n\n"
        "What would you like to do?"
    )


# ── Admin API ─────────────────────────────────────────────────
@app.get("/api/admin")
async def admin():
    return {
        "leads":             CRM_DB["leads"],
        "support_tickets":   CRM_DB["support_tickets"],
        "deals":             CRM_DB["deals"],
        "appointments":      CRM_DB["appointments"],
        "communication_log": CRM_DB["communication_log"],
        "stats": {
            "total_leads":   len(CRM_DB["leads"]),
            "total_tickets": len(CRM_DB["support_tickets"]),
            "total_deals":   len(CRM_DB["deals"]),
            "pipeline_value": sum(d["value"] for d in CRM_DB["deals"]),
        }
    }