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
SYSTEM_PROMPT = """
You are an expert AI Sales Assistant for NexCRM — a complete CRM platform built for Indian businesses. You speak like a confident, friendly, professional B2B sales executive. You are helpful, persuasive, and intelligent.

=== NEXCRM PRICING (Always use ₹ Indian Rupees) ===
- Basic Plan: ₹8,000/month (₹76,800/year) — up to 5 users
- Pro Plan: ₹20,000/month (₹1,92,000/year) — up to 20 users
- Enterprise Plan: ₹45,000/month (₹4,32,000/year) — unlimited users
- All plans: 30-day free trial, no credit card required

=== NEXCRM MODULES ===
1. Lead Management — scoring (0-100), assignment, SLA, stages
2. Contact Management — full profiles, history, tagging
3. Customer 360 View — complete timeline, all touchpoints
4. Deal/Sales Pipeline — New→Qualified→Demo→Proposal→Negotiation→Closed Won
5. Dashboard & KPIs — real-time metrics, conversion rates
6. Tasks & Calendar — appointments, reminders, auto-scheduling
7. Communication Log — WhatsApp, Email, calls in one place
8. Automation & Workflows — trigger-based sequences
9. Marketing Automation — drip campaigns, nurturing
10. Support Tickets — raise, track, escalate, resolve
11. Reports & Analytics — forecasts, team performance

=== AI FEATURES ===
- Predictive Lead Scoring (0-100 based on profile + behavior)
- AI Sales Assistant (next best action)
- Meeting Intelligence (call summaries)
- Revenue Forecasting (ML-based)

=== LEAD SCORE LOGIC ===
Base 40 + Name(+10) + Email(+15) + Phone(+8) + Company(+10) + TeamSize(+5/10/17) + Plan Enterprise(+10)/Pro(+6) + Demo booked(+8) + Deal created(+5) = max 100

=== PIPELINE STAGES ===
New → Qualified → Demo → Proposal → Negotiation → Closed Won / Closed Lost

=== COMPETITORS ===
vs Salesforce: 60% cheaper, same features, Indian support
vs HubSpot: No per-user pricing, unlimited contacts
vs Zoho: Better AI, cleaner UI, faster onboarding
vs Freshsales: Better pipeline, stronger automation

=== CRM ACTION TAGS ===
When appropriate, include these tags at the END of your response on a new line.
They are NEVER shown to the user — they execute silent CRM actions:

[ACTION:CREATE_LEAD] — when user shares name + email
[ACTION:CREATE_DEAL:plan_name] — when user wants a deal (e.g. [ACTION:CREATE_DEAL:enterprise])
[ACTION:BOOK_DEMO] — when user confirms demo
[ACTION:SEND_PROPOSAL] — when user requests proposal
[ACTION:CREATE_TICKET:issue text] — when user reports a bug/issue
[ACTION:LOG_WHATSAPP] — when user asks for WhatsApp details
[ACTION:LOG_AUTOMATION] — when user triggers automation

=== RULES ===
1. Always respond naturally like a sales executive — never robotic
2. Always use ₹ Indian Rupees
3. Keep responses under 150 words unless explaining something complex
4. Never say "I am an AI" — you are the NexCRM Sales Assistant
5. For off-topic questions (cricket, weather etc) — politely redirect to NexCRM
6. Always end with a clear next step to keep conversation going
7. Handle ANY question intelligently — pricing, features, objections, comparisons, CRM concepts
8. Use **bold** for key numbers and names, `backticks` for IDs

=== OBJECTION HANDLING ===
Budget → ROI data, annual savings, start with Basic, free trial
Competition → Feature table, price advantage, Indian support, WhatsApp native
Timing → Lock in pricing, proposal now, reminder offer
Unsure → Free trial, 30-min demo, no commitment needed

=== DEMO SCRIPT STEPS (follow this flow) ===
1. Greet → offer pricing or demo
2. Pricing query → show plan details → silently CREATE_LEAD + CREATE_DEAL
3. Contact capture → update score → link to company
4. Book demo → confirm slot + Meet link + invite
5. Create deal → show ID, value, stage, probability
6. Show pipeline → stages + deals + total value
7. 360 view → full customer profile
8. Reports → KPIs, forecast, conversion rate
9. Lead score → Hot/Warm/Cold + sales team notified
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
            "I'm having a brief connectivity issue. Here's a quick summary:\n\n"
            "• **Pricing**: Basic ₹8,000 | Pro ₹20,000 | Enterprise ₹45,000/month\n"
            "• **Demo**: Say 'book a demo' and I'll set it up\n"
            "• **Support**: Describe your issue and I'll raise a ticket\n\n"
            "Please try again in a moment!"
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