from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq          # GroqCloud official SDK
import re, random, os
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ─────────────────────────────────────────────────────────────
# GROQCLOUD CLIENT SETUP
# Set environment variable on Render: GROQ_API_KEY=gsk_xxxxx
# ─────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

COMPANY_NAME = "Future Invo Solutions"
COMPANY_URL = "https://futureinvo.com/"
ASSISTANT_NAME = "Future Invo CRM Assistant"

CRM_KEYWORDS = {
    "crm", "lead", "leads", "customer", "customers", "contact", "contacts",
    "deal", "deals", "pipeline", "sales", "support", "ticket", "tickets",
    "pricing", "price", "demo", "feature", "features", "automation",
    "workflow", "workflows", "dashboard", "report", "reports", "analytics",
    "integration", "integrations", "followup", "follow-up", "task", "tasks",
    "calendar", "whatsapp", "email", "login", "password", "bug", "issue",
    "error", "onboarding", "trial", "proposal", "invoice", "invoicing",
}

COMPETITOR_KEYWORDS = {
    "salesforce", "hubspot", "zoho", "freshsales", "pipedrive", "monday",
    "monday.com", "odoo", "microsoft dynamics", "dynamics 365",
}

FOLLOW_UP_HINTS = (
    "name", "email", "phone", "company", "team", "issue", "problem",
    "demo", "ticket", "contact", "pricing", "requirement",
)

# ─────────────────────────────────────────────────────────────
# REQUEST SCHEMA
# ─────────────────────────────────────────────────────────────
class UserMessage(BaseModel):
    message:  str
    user_id:  str
    state:    str  = "IDLE"
    data:     dict = {}
    history:  list = []

# ─────────────────────────────────────────────────────────────
# MOCK DATABASE
# ─────────────────────────────────────────────────────────────
CRM_DB = {
    "leads":             [],
    "deals":             [],
    "appointments":      [],
    "communication_log": [],
    "support_tickets":   [],
    "activities":        [],
}
LEAD_COUNTER   = [784]
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
EMAIL_RE  = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE  = re.compile(r"[\+]?[\d][\d\s\-]{8,13}\d")
TICKET_RE = re.compile(r"TICK-\d+", re.IGNORECASE)
NUM_RE    = re.compile(r"\b(\d+)\b")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def is_greeting_only(text: str) -> bool:
    normalized = normalize_text(text)
    return normalized in {
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
        "start", "start over", "reset", "restart", "help",
    }


def looks_like_follow_up(text: str, history: list, data: dict) -> bool:
    stripped = text.strip()
    lowered = normalize_text(text)
    if EMAIL_RE.search(stripped) or PHONE_RE.search(stripped) or TICKET_RE.search(stripped):
        return True
    if data:
        return True
    if len(lowered.split()) <= 5 and history:
        last_assistant = next(
            (turn.get("content", "") for turn in reversed(history) if turn.get("role") == "assistant"),
            "",
        ).lower()
        if any(hint in last_assistant for hint in FOLLOW_UP_HINTS):
            return True
    return False


def is_competitor_query(text: str) -> bool:
    lowered = normalize_text(text)
    if any(keyword in lowered for keyword in COMPETITOR_KEYWORDS):
        return True
    comparison_patterns = (
        "better than you", "better than your crm", "other crm", "another crm",
        "best crm", "compare crm", "compare with", "alternative to",
    )
    return any(pattern in lowered for pattern in comparison_patterns)


def is_crm_question(text: str, history: list, data: dict) -> bool:
    lowered = normalize_text(text)
    if is_greeting_only(lowered) or looks_like_follow_up(text, history, data):
        return True
    if any(keyword in lowered for keyword in CRM_KEYWORDS):
        return True
    crm_patterns = (
        "book a demo", "raise a ticket", "check ticket", "talk to sales",
        "talk to support", "customer relationship", "sales pipeline",
    )
    return any(pattern in lowered for pattern in crm_patterns)


def scope_redirect_response() -> str:
    return (
        "I can help with product features, demos, pricing requests, lead capture, "
        "support tickets, and related workflows. "
        "Please ask me something related to our services."
    )


def competitor_redirect_response() -> str:
    return (
        "We believe our CRM is the best choice for businesses that want a practical, "
        "professional solution with strong support and useful features. "
        "If you want, I can show you what makes us stand out."
    )


def is_pricing_query(text: str) -> bool:
    lowered = normalize_text(text)
    pricing_terms = ("pricing", "price", "prices", "plans", "cost", "quote", "package", "packages")
    return any(term in lowered for term in pricing_terms)


def is_feature_query(text: str) -> bool:
    lowered = normalize_text(text)
    feature_terms = ("features", "feature", "modules", "capabilities", "360 view", "pipeline")
    return any(term in lowered for term in feature_terms)


def is_explicit_demo_request(text: str) -> bool:
    lowered = normalize_text(text)
    demo_terms = (
        "book a demo", "schedule a demo", "i want a demo", "need a demo",
        "arrange a demo", "demo please", "book demo", "schedule demo",
    )
    return any(term in lowered for term in demo_terms)


def pricing_response() -> str:
    return (
        "**Pricing Plans**\n"
        f"- **Basic**: {fmt_inr(PLANS['basic']['monthly'])}/month for up to {PLANS['basic']['users']} users\n"
        f"- **Pro**: {fmt_inr(PLANS['pro']['monthly'])}/month for up to {PLANS['pro']['users']} users\n"
        f"- **Enterprise**: {fmt_inr(PLANS['enterprise']['monthly'])}/month for unlimited users\n\n"
        "All plans include a 30-day free trial. If you want, I can also help you choose the right plan."
    )


def features_response() -> str:
    return (
        "**Key Features**\n"
        "- Lead management with scoring and follow-up tracking\n"
        "- Customer 360 view with profiles and history\n"
        "- Sales pipeline for deals from new to closed\n"
        "- Tasks, calendar, and demo scheduling\n"
        "- Communication log for calls, email, and WhatsApp\n"
        "- Support ticket handling and status tracking\n"
        "- Reports, analytics, and workflow automation\n\n"
        "If you want, I can explain any feature in more detail."
    )


def leads_response() -> str:
    return (
        "**Lead Management**\n"
        "- Capture leads with name, email, phone, company, and team size\n"
        "- Score each lead automatically from 0 to 100\n"
        "- Track follow-ups and convert qualified leads into deals\n"
        "- Keep communication history in one place\n"
        "- Prioritize hot leads for the sales team\n\n"
        "If you want, I can also explain how lead scoring works."
    )


def pipeline_response() -> str:
    return (
        "**Sales Pipeline**\n"
        "- Track deals through **New -> Qualified -> Demo -> Proposal -> Negotiation -> Closed Won/Lost**\n"
        "- View deal value, stage, and win probability\n"
        "- Monitor total pipeline value and active opportunities\n"
        "- Move deals forward as the conversation progresses\n\n"
        "If you want, I can also explain each pipeline stage."
    )


def customer_360_response() -> str:
    return (
        "**Customer 360 View**\n"
        "- See the full customer profile in one place\n"
        "- Track contact details, company data, and team size\n"
        "- Review lead score, deal activity, and support history\n"
        "- Keep calls, email, WhatsApp, and notes connected to the same record\n\n"
        "If you want, I can show how this helps sales and support teams."
    )


def automation_response() -> str:
    return (
        "**Automation and Workflows**\n"
        "- Trigger follow-up actions automatically after lead capture\n"
        "- Schedule reminders, demo tasks, and proposal steps\n"
        "- Log communication activity across channels\n"
        "- Support structured handoff from sales to support\n\n"
        "If you want, I can explain the workflow examples in more detail."
    )


def support_response() -> str:
    return (
        "**Support and Ticketing**\n"
        "- Create support tickets for login issues, bugs, and account problems\n"
        "- Track tickets with a ticket ID such as `TICK-100`\n"
        "- Keep issue details linked to the customer record\n"
        "- Help the team review status and ongoing updates\n\n"
        "If you want, I can help create a support ticket right now."
    )


def is_lead_query(text: str) -> bool:
    lowered = normalize_text(text)
    lead_terms = ("lead", "leads", "lead scoring", "lead management", "follow-up", "follow up")
    return any(term in lowered for term in lead_terms)


def is_pipeline_query(text: str) -> bool:
    lowered = normalize_text(text)
    pipeline_terms = ("pipeline", "deal stage", "deal stages", "sales stages", "sales pipeline")
    return any(term in lowered for term in pipeline_terms)


def is_customer_360_query(text: str) -> bool:
    lowered = normalize_text(text)
    customer_terms = ("360 view", "customer 360", "customer profile", "full customer profile")
    return any(term in lowered for term in customer_terms)


def is_automation_query(text: str) -> bool:
    lowered = normalize_text(text)
    automation_terms = ("automation", "workflow", "workflows", "automatic follow-up", "automated follow-up")
    return any(term in lowered for term in automation_terms)


def is_support_query(text: str) -> bool:
    lowered = normalize_text(text)
    support_terms = ("support", "ticket", "tickets", "issue", "issues", "bug", "bugs", "login")
    return any(term in lowered for term in support_terms)

# ─────────────────────────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────────────────────────
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

def fmt_inr(amount: int) -> str:
    return f"₹{amount/100000:.1f} Lakhs" if amount >= 100000 else f"₹{amount:,}"

def save_lead(data: dict) -> str:
    lid   = f"lead_{LEAD_COUNTER[0]}"
    LEAD_COUNTER[0] += 1
    score = calc_lead_score(data)
    CRM_DB["leads"].append({
        **{k: v for k, v in data.items()},
        "lead_id": lid, "lead_score": score,
        "stage": "New", "created": datetime.now().strftime("%d %b %Y %H:%M")
    })
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
    demo_dt = datetime.now() + timedelta(days=3)
    while demo_dt.weekday() != 2:
        demo_dt += timedelta(days=1)
    date_str = demo_dt.strftime("%A, %d %B")
    aid = f"apt_{random.randint(100, 999)}"
    apt = {
        "id": aid, "name": data.get("name", "—"),
        "email": data.get("email", "—"), "date": date_str,
        "time": "11:00 AM", "meet": f"https://meet.google.com/crm-{aid}"
    }
    CRM_DB["appointments"].append(apt)
    log_activity(data, f"Demo booked: {date_str}")
    return apt

def log_comm(data: dict, channel: str, note: str):
    CRM_DB["communication_log"].append({
        "name": data.get("name", "—"), "channel": channel,
        "note": note, "time": datetime.now().strftime("%d %b %Y %H:%M")
    })

def log_activity(data: dict, action: str):
    CRM_DB["activities"].append({
        "name": data.get("name", "—"), "action": action,
        "time": datetime.now().strftime("%d %b %Y %H:%M")
    })

# ─────────────────────────────────────────────────────────────
# CRM CONTEXT SNAPSHOT FOR AI
# ─────────────────────────────────────────────────────────────
def build_crm_context(data: dict, state: str) -> str:
    score  = calc_lead_score(data)
    plan   = data.get("plan", "not selected")
    p_info = PLANS.get(plan, None)
    price  = f"₹{p_info['monthly']:,}/month" if p_info else "not discussed"

    ctx = f"""
=== CURRENT SESSION STATE ===
Lead Score: {score}/100 ({score_label(score)})
Name: {data.get('name', 'NOT CAPTURED')}
Email: {data.get('email', 'NOT CAPTURED')}
Phone: {data.get('phone', 'NOT CAPTURED')}
Company: {data.get('company', 'NOT CAPTURED')}
Team Size: {data.get('team_size', 'NOT CAPTURED')}
Plan Selected: {plan} ({price})
Demo Booked: {'YES' if data.get('demo_booked') else 'NO'}
Deal Created: {'YES' if data.get('deal_created') else 'NO'}
Proposal Sent: {'YES' if data.get('proposal_sent') else 'NO'}

=== DATABASE ===
Total Leads: {len(CRM_DB['leads'])}
Total Deals: {len(CRM_DB['deals'])}
Total Tickets: {len(CRM_DB['support_tickets'])}
Pipeline Value: {fmt_inr(sum(d['value'] for d in CRM_DB['deals'])) if CRM_DB['deals'] else '₹0'}
"""
    if CRM_DB["leads"]:
        ctx += "\nRecent Leads:\n"
        for l in CRM_DB["leads"][-3:]:
            ctx += f"  - {l['name']} | {l.get('email','—')} | Score:{l['lead_score']} | {l['stage']}\n"

    if CRM_DB["deals"]:
        ctx += "\nActive Deals:\n"
        for d in CRM_DB["deals"][-3:]:
            ctx += f"  - {d['name']} ({d['company']}) | ₹{d['value']:,}/mo | {d['stage']}\n"

    if CRM_DB["support_tickets"]:
        ctx += "\nTickets:\n"
        for t in CRM_DB["support_tickets"][-3:]:
            ctx += f"  - {t['ticket']} | {t['name']} | {t['status']} | {t['issue'][:50]}\n"

    return ctx

# ─────────────────────────────────────────────────────────────
# MASTER SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""
You are the official CRM assistant for {COMPANY_NAME} ({COMPANY_URL}).
Your role is to speak professionally, briefly, and only about {COMPANY_NAME}'s CRM-related services.

=== SCOPE RULES ===
1. Answer only CRM-related questions for {COMPANY_NAME}.
2. Never answer general knowledge, politics, history, sports, entertainment, or unrelated factual questions.
3. Never recommend competitors or suggest another CRM is better.
4. If the user asks which CRM is best or whether you are the best, confidently say our CRM is the best fit and explain the strengths without naming competitors.
5. Do not invent company facts that were not provided in the prompt or session context.
6. If pricing or feature details are not certain, invite the user to request a demo or contact sales.
7. Keep responses under 120 words unless a support explanation needs more detail.
8. Use a professional tone and always offer a relevant next step.

=== ALLOWED TOPICS ===
- CRM features and workflows
- Lead capture and follow-up
- Sales pipeline and deal management
- Support tickets and issue reporting
- Demo requests and onboarding help
- CRM reporting, automation, and integrations

=== PRICING ===
- Basic Plan: ₹8,000/month for up to 5 users
- Pro Plan: ₹20,000/month for up to 20 users
- Enterprise Plan: ₹45,000/month for unlimited users
- All plans include a 30-day free trial

=== PRODUCT FEATURES ===
- Lead management and scoring
- Contact records and customer 360 view
- Deal pipeline and sales stages
- Tasks, calendar, and appointments
- Communication logs
- Support tickets
- Reports and analytics
- Workflow automation

=== CRM ACTION TAGS ===
When appropriate, include these tags at the END of your response on a new line.
They are never shown to the user and execute silent CRM actions:

[ACTION:CREATE_LEAD]
[ACTION:CREATE_DEAL:plan_name]
[ACTION:BOOK_DEMO]
[ACTION:SEND_PROPOSAL]
[ACTION:CREATE_TICKET:issue text]
[ACTION:LOG_WHATSAPP]
[ACTION:LOG_AUTOMATION]

=== RESPONSE STYLE ===
- Refer to the business as {COMPANY_NAME}
- Stay specific to CRM assistance
- Prefer clear, direct wording over marketing hype
- Use **bold** for important labels and `backticks` for IDs
- Do not repeat the company name unless it adds clear value
- Give exact pricing when the user asks for pricing
- Do not use [ACTION:BOOK_DEMO] unless the user clearly asks to book or schedule a demo
"""

# ─────────────────────────────────────────────────────────────
# PROCESS ACTION TAGS FROM AI RESPONSE
# ─────────────────────────────────────────────────────────────
def process_actions(response_text: str, data: dict, user_message: str) -> tuple:
    crm_confirmations = []

    # Extract entities from user message
    email_m = EMAIL_RE.search(user_message)
    phone_m = PHONE_RE.search(user_message)
    if email_m: data["email"] = email_m.group()
    if phone_m: data["phone"] = phone_m.group()

    name_match = re.search(
        r"(?:my name is|i am|i'm|this is)\s+([A-Z][a-z]+(?: [A-Z][a-z]+)?)",
        user_message, re.IGNORECASE
    )
    if name_match and not data.get("name"):
        data["name"] = name_match.group(1).strip()

    co_match = re.search(
        r"(?:company is|from|at|working at)\s+([A-Za-z][a-zA-Z\s]+?)(?:\s*,|\s*\.|$)",
        user_message, re.IGNORECASE
    )
    if co_match and not data.get("company"):
        candidate = co_match.group(1).strip()
        if len(candidate.split()) <= 4:
            data["company"] = candidate

    ts_match = re.search(
        r"(\d+)\s*(?:users?|people|members?|team members?|employees?)",
        user_message, re.IGNORECASE
    )
    if ts_match and not data.get("team_size"):
        data["team_size"] = ts_match.group(1)

    if not data.get("plan"):
        low = user_message.lower()
        if "enterprise" in low: data["plan"] = "enterprise"
        elif "pro"       in low: data["plan"] = "pro"
        elif "basic"     in low: data["plan"] = "basic"

    # Parse and execute action tags
    action_pattern = re.compile(r'\[ACTION:([^\]]+)\]', re.IGNORECASE)
    actions = action_pattern.findall(response_text)

    for action in actions:
        action_upper = action.upper().strip()

        if action_upper == "CREATE_LEAD":
            if data.get("name") and data.get("email"):
                existing = any(l.get("email") == data["email"] for l in CRM_DB["leads"])
                if not existing:
                    lid   = save_lead(data)
                    score = calc_lead_score(data)
                    data["lead_id"] = lid
                    crm_confirmations.append(
                        f"✅ Lead created successfully *(ID: `{lid}`)*\n"
                        f"✅ Lead linked to **{data.get('company', 'your company')}**\n"
                        f"🎯 Lead Score: **{score}/100** — {score_label(score)}"
                    )

        elif action_upper.startswith("CREATE_DEAL"):
            parts = action.split(":", 1)
            plan  = parts[1].lower().strip() if len(parts) > 1 else data.get("plan", "pro")
            if plan not in PLANS:
                if "enterprise" in plan: plan = "enterprise"
                elif "pro"      in plan: plan = "pro"
                else:                    plan = "basic"
            data["plan"] = plan
            p     = PLANS[plan]
            did   = save_deal(data, p["monthly"])
            data["deal_id"]      = did
            data["deal_created"] = True
            score = calc_lead_score(data)
            crm_confirmations.append(
                f"✅ Deal created in pipeline *(ID: `{did}`)*\n"
                f"💼 Deal Value: **₹{p['monthly']:,}/month**\n"
                f"📋 Stage: **Proposal** | Probability: **75%**\n"
                f"🎯 Lead Score: **{score}/100** — {score_label(score)}"
            )

        elif action_upper == "BOOK_DEMO":
            if is_explicit_demo_request(user_message):
                apt  = book_apt(data)
                data["demo_booked"] = True
                log_comm(data, "System", f"Demo booked: {apt['date']}")
                score = calc_lead_score(data)
                crm_confirmations.append(
                    f"✅ Task created: Demo with **{data.get('name', 'you')}**\n"
                    f"✅ Appointment: **{apt['date']} at {apt['time']}**\n"
                    f"✅ Google Meet: `{apt['meet']}`\n"
                    f"✅ Calendar invite sent to **{data.get('email', 'your email')}**\n"
                    f"🎯 Lead Score updated: **{score}/100** — {score_label(score)}"
                )

        elif action_upper == "SEND_PROPOSAL":
            plan = data.get("plan", "pro")
            p    = PLANS.get(plan, PLANS["pro"])
            log_comm(data, "Email", "Proposal sent")
            data["proposal_sent"] = True
            crm_confirmations.append(
                f"✅ Proposal emailed to **{data.get('email', 'you')}**\n"
                f"📄 Plan: **{p['label']}** — ₹{p['monthly']:,}/month"
            )

        elif action_upper.startswith("CREATE_TICKET"):
            parts = action.split(":", 1)
            issue = parts[1].strip() if len(parts) > 1 else "General support request"
            tid   = save_ticket(data, issue)
            crm_confirmations.append(
                f"🎫 Support ticket created: `{tid}`\n"
                f"📋 Status: 🟡 Open — response within 24 hours"
            )

        elif action_upper == "LOG_WHATSAPP":
            plan = data.get("plan", "pro")
            p    = PLANS.get(plan, PLANS["pro"])
            log_comm(data, "WhatsApp", "Details sent via WhatsApp")
            crm_confirmations.append(
                f"📱 Details sent on WhatsApp!\n"
                f"✅ Plan: **{p['label']}** — ₹{p['monthly']:,}/month"
            )

        elif action_upper == "LOG_AUTOMATION":
            log_comm(data, "Automation", "Nurture sequence triggered")
            log_activity(data, "Automation workflow triggered")
            crm_confirmations.append(
                f"⚡ Automation triggered!\n"
                f"✅ Lead nurture sequence started\n"
                f"✅ Follow-up email scheduled for tomorrow 10:00 AM\n"
                f"✅ Sales manager notified via Slack\n"
                f"✅ Task created: Follow-up call within 24 hours"
            )

    # Strip action tags from visible response
    clean_response = action_pattern.sub("", response_text).strip()

    # Append CRM confirmations
    if crm_confirmations:
        clean_response += "\n\n" + "\n\n".join(crm_confirmations)

    return clean_response, data

# ─────────────────────────────────────────────────────────────
# MAIN ENDPOINT
# ─────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(msg: UserMessage):
    raw     = msg.message.strip()
    state   = msg.state
    data    = dict(msg.data)
    history = list(msg.history)

    if is_competitor_query(raw):
        return {
            "response": competitor_redirect_response(),
            "state": "IDLE",
            "data": data,
        }

    if not is_crm_question(raw, history, data):
        return {
            "response": scope_redirect_response(),
            "state": "IDLE",
            "data": data,
        }

    if is_pricing_query(raw):
        return {
            "response": pricing_response(),
            "state": "IDLE",
            "data": data,
        }

    if is_feature_query(raw):
        return {
            "response": features_response(),
            "state": "IDLE",
            "data": data,
        }

    if is_lead_query(raw):
        return {
            "response": leads_response(),
            "state": "IDLE",
            "data": data,
        }

    if is_pipeline_query(raw):
        return {
            "response": pipeline_response(),
            "state": "IDLE",
            "data": data,
        }

    if is_customer_360_query(raw):
        return {
            "response": customer_360_response(),
            "state": "IDLE",
            "data": data,
        }

    if is_automation_query(raw):
        return {
            "response": automation_response(),
            "state": "IDLE",
            "data": data,
        }

    if is_support_query(raw) and not is_explicit_demo_request(raw):
        return {
            "response": support_response(),
            "state": "IDLE",
            "data": data,
        }

    # Direct ticket lookup — no AI needed
    ticket_match = TICKET_RE.search(raw)
    if ticket_match:
        tid   = ticket_match.group().upper()
        found = next((t for t in CRM_DB["support_tickets"] if t["ticket"] == tid), None)
        if found:
            return {
                "response": (
                    f"🎫 **Ticket: {found['ticket']}**\n\n"
                    f"• Customer: **{found['name']}**\n"
                    f"• Email: {found['email']}\n"
                    f"• Issue: {found['issue']}\n"
                    f"• Status: 🟡 **In Progress**\n\n"
                    "Our support team is actively working on this."
                ),
                "state": "IDLE", "data": data
            }

    # Build CRM context
    crm_context = build_crm_context(data, state)

    # Build messages for GroqCloud
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\n" + crm_context
        }
    ]

    # Add last 10 turns of history
    for turn in history[-10:]:
        if turn.get("role") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})

    # Add current message
    messages.append({"role": "user", "content": raw})

    # Call GroqCloud API
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # Best model on GroqCloud — fast + smart
            messages=messages,
            max_tokens=600,
            temperature=0.7,
        )
        ai_response = completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"Groq API error: {e}")
        ai_response = (
            "I am having a brief connectivity issue right now.\n\n"
            "I can still help with CRM demos, support tickets, lead capture, and feature-related questions.\n"
            "Please try your CRM question again in a moment."
        )

    # Process CRM actions silently
    clean_response, updated_data = process_actions(ai_response, data, raw)

    return {
        "response": clean_response,
        "state":    "IDLE",
        "data":     updated_data,
    }

# ─────────────────────────────────────────────────────────────
# ADMIN API
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
