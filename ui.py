from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI          # Grok uses OpenAI-compatible SDK
import re, random, os
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ─────────────────────────────────────────────────────────────
# GROK CLIENT SETUP
# Replace YOUR_GROK_API_KEY with your actual key
# OR set environment variable: GROK_API_KEY=xai-xxxxx
# ─────────────────────────────────────────────────────────────
GROK_API_KEY = os.environ.get("GROK_API_KEY", "YOUR_GROK_API_KEY")

grok_client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1",
)

# ─────────────────────────────────────────────────────────────
# REQUEST SCHEMA
# ─────────────────────────────────────────────────────────────
class UserMessage(BaseModel):
    message:  str
    user_id:  str
    state:    str  = "IDLE"
    data:     dict = {}
    history:  list = []   # Full conversation history for context

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
# BUILD CRM CONTEXT SNAPSHOT
# This tells Grok what has already happened in this session
# ─────────────────────────────────────────────────────────────
def build_crm_context(data: dict, state: str) -> str:
    score   = calc_lead_score(data)
    plan    = data.get("plan", "not selected")
    p_info  = PLANS.get(plan, None)
    price   = f"₹{p_info['monthly']:,}/month" if p_info else "not discussed"

    ctx = f"""
=== CURRENT CRM SESSION STATE ===
Conversation State: {state}
Lead Score: {score}/100 ({score_label(score)})

Contact Info Captured:
- Name: {data.get('name', 'NOT YET CAPTURED')}
- Email: {data.get('email', 'NOT YET CAPTURED')}
- Phone: {data.get('phone', 'NOT YET CAPTURED')}
- Company: {data.get('company', 'NOT YET CAPTURED')}
- Team Size: {data.get('team_size', 'NOT YET CAPTURED')}
- Industry: {data.get('industry', 'NOT YET CAPTURED')}

Deal Info:
- Plan Selected: {plan}
- Price: {price}
- Demo Booked: {'YES' if data.get('demo_booked') else 'NO'}
- Deal Created: {'YES' if data.get('deal_created') else 'NO'}
- Proposal Sent: {'YES' if data.get('proposal_sent') else 'NO'}

=== CRM DATABASE SNAPSHOT ===
Total Leads in DB: {len(CRM_DB['leads'])}
Total Deals in DB: {len(CRM_DB['deals'])}
Total Tickets in DB: {len(CRM_DB['support_tickets'])}
Pipeline Value: {fmt_inr(sum(d['value'] for d in CRM_DB['deals'])) if CRM_DB['deals'] else '₹0'}
"""

    if CRM_DB["leads"]:
        ctx += "\nRecent Leads:\n"
        for l in CRM_DB["leads"][-3:]:
            ctx += f"  - {l['name']} | {l.get('email','—')} | Score: {l['lead_score']} | Stage: {l['stage']}\n"

    if CRM_DB["deals"]:
        ctx += "\nActive Deals:\n"
        for d in CRM_DB["deals"][-3:]:
            ctx += f"  - {d['name']} ({d['company']}) | ₹{d['value']:,}/mo | Stage: {d['stage']}\n"

    if CRM_DB["support_tickets"]:
        ctx += "\nSupport Tickets:\n"
        for t in CRM_DB["support_tickets"][-3:]:
            ctx += f"  - {t['ticket']} | {t['name']} | Status: {t['status']} | Issue: {t['issue'][:50]}\n"

    return ctx

# ─────────────────────────────────────────────────────────────
# MASTER SYSTEM PROMPT FOR GROK
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are an expert AI Sales Assistant for NexCRM — a complete Customer Relationship Management platform built for Indian businesses. You are highly intelligent, conversational, and persuasive like a professional B2B sales executive.

=== YOUR PERSONALITY ===
- Friendly, confident, and professional — like a senior sales executive
- Empathetic — you understand business challenges
- Persuasive — you handle objections with data and logic
- Smart — you remember context and give personalized responses
- Natural — you never sound robotic or scripted

=== NEXCRM PRODUCT KNOWLEDGE ===

PRICING PLANS (Always use ₹ Indian Rupees):
- Basic Plan: ₹8,000/month (₹76,800/year) — up to 5 users
- Pro Plan: ₹20,000/month (₹1,92,000/year) — up to 20 users  
- Enterprise Plan: ₹45,000/month (₹4,32,000/year) — unlimited users
- All plans include 30-day free trial, no credit card required

CORE MODULES:
1. Lead Management — scoring, assignment, SLA tracking, stages (New→Qualified→Demo→Proposal→Closed)
2. Contact Management — full profile, communication history, tagging
3. Customer 360 View — complete timeline, all touchpoints, predictive insights
4. Deal/Sales Pipeline — visual kanban, forecasting, probability scoring
5. Dashboard & KPIs — real-time metrics, conversion rates, revenue tracking
6. Tasks & Calendar — appointments, reminders, auto-scheduling
7. Communication Log — WhatsApp, Email, calls all in one place
8. Automation & Workflows — trigger-based actions, drip campaigns
9. Marketing Automation — email campaigns, lead nurturing sequences
10. Support Tickets — raise, track, escalate, resolve
11. Reports & Analytics — revenue forecasts, team performance, pipeline health

AI FEATURES:
- Predictive Lead Scoring (0-100 score based on behavior and profile)
- AI Sales Assistant — next best action recommendations
- Meeting Intelligence — call summaries, action items
- Revenue Forecasting — ML-based pipeline predictions

LEAD SCORING LOGIC:
- Base score: 40
- Name captured: +10
- Email captured: +15
- Phone captured: +8
- Company captured: +10
- Team size (small +5, medium +10, large +17)
- Enterprise plan: +10, Pro plan: +6
- Demo booked: +8
- Deal created: +5
- Max: 100

HOW THE PIPELINE WORKS:
Stage 1 (New): Lead just created from initial contact
Stage 2 (Qualified): Lead has shared contact details and shown intent
Stage 3 (Demo): Demo has been scheduled or completed
Stage 4 (Proposal): Quote/proposal has been sent
Stage 5 (Negotiation): Discussion on pricing/terms
Stage 6 (Closed Won): Deal signed and payment received
Stage 7 (Closed Lost): Deal not converted

COMPETITORS COMPARISON:
vs Salesforce: 60% cheaper, same enterprise features, Indian support
vs HubSpot: No per-user pricing, unlimited contacts, better for SMBs
vs Zoho: Better AI features, cleaner UI, faster onboarding
vs Freshsales: Better pipeline visualization, stronger automation

=== CRM ACTION TRIGGERS ===
When the user's message warrants it, you MUST include these exact action tags in your response.
These tags are parsed silently and execute CRM actions in the background:

[ACTION:CREATE_LEAD] — When user shares their name AND email
[ACTION:CREATE_DEAL:plan_name] — When user wants to buy/create deal (e.g. [ACTION:CREATE_DEAL:enterprise])
[ACTION:BOOK_DEMO] — When user confirms they want to book a demo
[ACTION:SEND_PROPOSAL] — When user requests a proposal
[ACTION:CREATE_TICKET:issue description] — When user reports a bug/issue
[ACTION:LOG_WHATSAPP] — When user asks to send details on WhatsApp
[ACTION:LOG_AUTOMATION] — When user asks to trigger automation

IMPORTANT: Place action tags at the END of your response, on their own line.
The user will NEVER see these tags — they are stripped before displaying.

=== CONVERSATION RULES ===

1. ALWAYS respond in a natural, conversational way — never bullet-point dump
2. ALWAYS use ₹ Indian Rupees for all prices
3. When a prospect gives pricing query with plan + team size → CREATE_LEAD + CREATE_DEAL silently
4. When capturing contact info → UPDATE context and CREATE_LEAD when you have name + email
5. Never say "I am an AI" — you are the NexCRM Sales Assistant
6. Handle ANY question about CRM, sales, business, pricing naturally
7. For completely off-topic questions (cricket, weather etc) — politely redirect to NexCRM
8. Always end with a clear next step or question to keep conversation going
9. Keep responses concise but complete — max 150 words unless explaining a complex topic
10. Use emojis sparingly — only where they genuinely add warmth

=== OBJECTION HANDLING ===
Budget objection → ROI data, payment flexibility, free trial, start small with Basic
Competition → Feature comparison, price advantage, Indian support, native WhatsApp
Timing → Lock in pricing, reminder offer, proposal now decide later
Not sure → Case studies, free trial, 30-min demo with no commitment

=== DEMO SCRIPT (For Reference) ===
Step 1: Greet → offer pricing or demo
Step 2: Pricing inquiry → show plan + silently create lead + deal
Step 3: Contact capture → update lead + show score
Step 4: Book demo → confirm slot, Meet link, calendar invite
Step 5: Create deal → show deal ID, value, stage, probability
Step 6: Show pipeline → visual stages + deals
Step 7: 360 view → complete customer profile
Step 8: Reports → KPIs, forecast, conversion
Step 9: Lead score → Hot/Warm/Cold label

=== RESPONSE FORMAT ===
- Respond naturally like a sales executive
- For structured data (tables, pipeline) use markdown formatting
- Bold key numbers and names with **double asterisks**
- Use backticks for IDs: `lead_784`
- Always include action tags at the bottom when applicable
"""

# ─────────────────────────────────────────────────────────────
# EXTRACT AND EXECUTE ACTIONS FROM GROK RESPONSE
# ─────────────────────────────────────────────────────────────
def extract_entities_from_text(text: str, data: dict) -> dict:
    """Extract name, email, phone, company from Grok's response context"""
    email_m = EMAIL_RE.search(text)
    phone_m = PHONE_RE.search(text)
    if email_m and not data.get("email"):
        data["email"] = email_m.group()
    if phone_m and not data.get("phone"):
        data["phone"] = phone_m.group()
    return data

def extract_plan_from_text(text: str) -> str:
    low = text.lower()
    if "enterprise" in low: return "enterprise"
    if "pro"        in low: return "pro"
    if "basic"      in low: return "basic"
    return "pro"

def process_actions(response_text: str, data: dict, user_message: str) -> tuple[str, dict, str]:
    """
    Parse [ACTION:...] tags from Grok response.
    Execute CRM operations silently.
    Return cleaned response text, updated data, updated state.
    """
    state = "IDLE"
    crm_confirmations = []

    # Extract email/phone from user message too
    email_m = EMAIL_RE.search(user_message)
    phone_m = PHONE_RE.search(user_message)
    if email_m: data["email"] = email_m.group()
    if phone_m: data["phone"] = phone_m.group()

    # Parse name from "my name is X" or "I am X"
    name_match = re.search(
        r"(?:my name is|i am|i'm|this is)\s+([A-Z][a-z]+(?: [A-Z][a-z]+)?)",
        user_message, re.IGNORECASE
    )
    if name_match and not data.get("name"):
        data["name"] = name_match.group(1).strip()

    # Parse company from "company is X" or "from X"
    co_match = re.search(
        r"(?:company is|from|at|working at)\s+([A-Z][a-zA-Z\s]+?)(?:\s*,|\s*\.|$)",
        user_message, re.IGNORECASE
    )
    if co_match and not data.get("company"):
        candidate = co_match.group(1).strip()
        if len(candidate.split()) <= 4:
            data["company"] = candidate

    # Parse team size
    ts_match = re.search(r"(\d+)\s*(?:users?|people|members?|team members?|employees?)", user_message, re.IGNORECASE)
    if ts_match and not data.get("team_size"):
        data["team_size"] = ts_match.group(1)

    # Parse plan from user message
    if not data.get("plan"):
        plan = extract_plan_from_text(user_message)
        if any(p in user_message.lower() for p in ["enterprise", "pro", "basic"]):
            data["plan"] = plan

    # Process action tags from Grok response
    action_pattern = re.compile(r'\[ACTION:([^\]]+)\]', re.IGNORECASE)
    actions = action_pattern.findall(response_text)

    for action in actions:
        action_upper = action.upper().strip()

        if action_upper == "CREATE_LEAD" and data.get("name") and data.get("email"):
            # Don't create duplicate leads
            existing = any(l.get("email") == data["email"] for l in CRM_DB["leads"])
            if not existing:
                lid = save_lead(data)
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
            plan  = plan if plan in PLANS else extract_plan_from_text(plan)
            data["plan"] = plan
            p     = PLANS.get(plan, PLANS["pro"])
            did   = save_deal(data, p["monthly"])
            data["deal_id"] = did
            data["deal_created"] = True
            score = calc_lead_score(data)
            crm_confirmations.append(
                f"✅ Deal created in pipeline *(ID: `{did}`)*\n"
                f"💼 Deal Value: **₹{p['monthly']:,}/month**\n"
                f"📋 Stage: **Proposal** | Probability: **75%**\n"
                f"🎯 Lead Score: **{score}/100** — {score_label(score)}"
            )

        elif action_upper == "BOOK_DEMO":
            apt  = book_apt(data)
            data["demo_booked"] = True
            data["apt_id"] = apt["id"]
            score = calc_lead_score(data)
            log_comm(data, "System", f"Demo booked: {apt['date']}")
            crm_confirmations.append(
                f"✅ Task created: Demo with **{data.get('name', 'you')}**\n"
                f"✅ Appointment: **{apt['date']} at {apt['time']}**\n"
                f"✅ Google Meet: `{apt['meet']}`\n"
                f"✅ Calendar invite sent to **{data.get('email', 'your email')}**\n"
                f"🎯 Lead Score: **{score}/100** — {score_label(score)}"
            )

        elif action_upper == "SEND_PROPOSAL":
            plan = data.get("plan", "pro")
            p    = PLANS.get(plan, PLANS["pro"])
            log_comm(data, "Email", "Proposal sent")
            data["proposal_sent"] = True
            log_activity(data, "Proposal emailed")
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
                f"✅ Message delivered to your registered number"
            )

        elif action_upper == "LOG_AUTOMATION":
            log_comm(data, "Automation", "Nurture sequence triggered")
            log_activity(data, "Automation workflow triggered")
            crm_confirmations.append(
                f"⚡ Automation triggered!\n"
                f"✅ Lead nurture sequence started\n"
                f"✅ Follow-up email scheduled for tomorrow 10:00 AM\n"
                f"✅ Sales manager notified via Slack"
            )

    # Remove action tags from visible response
    clean_response = action_pattern.sub("", response_text).strip()

    # Append CRM confirmations to response
    if crm_confirmations:
        clean_response += "\n\n" + "\n\n".join(crm_confirmations)

    return clean_response, data, state

# ─────────────────────────────────────────────────────────────
# MAIN ENDPOINT
# ─────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(msg: UserMessage):
    raw     = msg.message.strip()
    state   = msg.state
    data    = dict(msg.data)
    history = list(msg.history)  # Full conversation history

    # ── Ticket lookup (handle directly, no need for Grok) ────
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

    # ── Build CRM context snapshot ────────────────────────────
    crm_context = build_crm_context(data, state)

    # ── Build messages array for Grok ────────────────────────
    # System prompt + CRM context
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\n" + crm_context
        }
    ]

    # Add conversation history (last 10 turns to stay within context)
    for turn in history[-10:]:
        if turn.get("role") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})

    # Add current user message
    messages.append({"role": "user", "content": raw})

    # ── Call Grok API ─────────────────────────────────────────
    try:
        completion = grok_client.chat.completions.create(
            model="grok-3-mini",          # Fast and smart, use grok-3 for max intelligence
            messages=messages,
            max_tokens=600,
            temperature=0.7,              # Balanced: creative but accurate
        )
        grok_response = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Grok API error: {e}")
        grok_response = (
            "I'm having a brief connectivity issue. Let me help you directly:\n\n"
            "• **Pricing**: Basic ₹8,000 | Pro ₹20,000 | Enterprise ₹45,000/month\n"
            "• **Demo**: Just say 'book a demo' and I'll set it up\n"
            "• **Support**: Describe your issue and I'll raise a ticket\n\n"
            "Please try again in a moment!"
        )

    # ── Process CRM actions silently ─────────────────────────
    clean_response, updated_data, new_state = process_actions(grok_response, data, raw)

    return {
        "response": clean_response,
        "state":    new_state,
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