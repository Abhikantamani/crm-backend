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

COMPANY_NAME = "Future Invo Solutions"

CRM_DB = {
    "leads": [],
    "support_tickets": [],
}

USER_STATE = {}
USER_DATA = {}

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
TICKET_RE = re.compile(r"tick-\d+", re.IGNORECASE)


class ChatMessage(BaseModel):
    message: str
    user_id: str


def welcome_response() -> dict:
    return {
        "response": (
            "Hello! I am your CRM bot from Future Invo Solutions.\n\n"
            "I can help with pricing, features, demos, lead handling, support tickets, and onboarding.\n\n"
            "You can ask me about:\n"
            "- **Pricing, features, and demos**\n"
            "- **Technical issues and login help**\n"
            "- **Ticket status** (for example: `Check TICK-100`)"
        )
    }


def is_competitor_query(msg: str) -> bool:
    lowered = msg.lower()
    competitor_terms = [
        "salesforce", "hubspot", "zoho", "freshsales", "pipedrive",
        "better than you", "other crm", "best crm", "compare",
    ]
    return any(term in lowered for term in competitor_terms)


def is_crm_related(msg: str) -> bool:
    lowered = msg.lower()
    crm_terms = [
        "crm", "pricing", "price", "feature", "demo", "sales", "lead",
        "support", "ticket", "login", "password", "bug", "issue", "error",
        "customer", "pipeline", "deal", "automation", "report",
    ]
    return any(term in lowered for term in crm_terms)


@app.post("/chat")
async def chat_endpoint(payload: ChatMessage):
    raw_msg = payload.message.strip()
    msg = raw_msg.lower()
    user_id = payload.user_id

    if any(word in msg.split() for word in ["hi", "hello", "hey", "cancel", "menu", "reset", "restart"]) or "start over" in msg:
        USER_STATE[user_id] = None
        USER_DATA[user_id] = {}
        return welcome_response()

    current_state = USER_STATE.get(user_id)

    if current_state is None and is_competitor_query(raw_msg):
        return {
            "response": (
                "Our CRM is the best choice if you want a practical system with strong features, "
                "smooth lead handling, and dependable support. "
                "If you want, I can walk you through what makes it stand out."
            )
        }

    if current_state is None and any(word in msg for word in ["price", "pricing", "cost", "plans"]):
        return {
            "response": (
                "**Pricing Plans**\n"
                "- **Basic**: ₹8,000/month for up to 5 users\n"
                "- **Pro**: ₹20,000/month for up to 20 users\n"
                "- **Enterprise**: ₹45,000/month for unlimited users\n\n"
                "All plans include a 30-day free trial."
            )
        }

    if current_state is None and any(word in msg for word in ["feature", "features", "pipeline", "360"]):
        return {
            "response": (
                "**Key Features**\n"
                "- Lead management and scoring\n"
                "- Customer 360 view\n"
                "- Sales pipeline tracking\n"
                "- Tasks and calendar\n"
                "- Support tickets\n"
                "- Reports and automation"
            )
        }

    if current_state is None and any(word in msg for word in ["lead", "leads", "lead scoring"]):
        return {
            "response": (
                "**Lead Management**\n"
                "- Capture lead details and contact information\n"
                "- Score leads automatically\n"
                "- Track follow-ups and handoff to deals\n"
                "- Keep communication history connected to each lead"
            )
        }

    if current_state is None and any(word in msg for word in ["pipeline", "deal stage", "sales stage"]):
        return {
            "response": (
                "**Sales Pipeline**\n"
                "- New -> Qualified -> Demo -> Proposal -> Negotiation -> Closed Won/Lost\n"
                "- Track deal value, stage, and win probability\n"
                "- Monitor active opportunities across the pipeline"
            )
        }

    if current_state is None and any(word in msg for word in ["360", "customer profile"]):
        return {
            "response": (
                "**Customer 360 View**\n"
                "- Keep customer details in one place\n"
                "- View support history, lead activity, and communication records\n"
                "- Help sales and support teams work from the same profile"
            )
        }

    if current_state is None and not is_crm_related(raw_msg):
        return {
            "response": (
                "I can help with features, demos, support, pricing requests, or ticket status."
            )
        }

    if current_state == "WAITING_FOR_LEAD_NAME":
        if len(raw_msg.split()) > 3:
            return {"response": "That seems a bit long for a name. Please share your first name only."}

        USER_DATA[user_id] = {"name": raw_msg.title()}
        USER_STATE[user_id] = "WAITING_FOR_LEAD_EMAIL"
        return {"response": f"Nice to meet you, {raw_msg.title()}. What is the best **email address** to reach you at?"}

    if current_state == "WAITING_FOR_LEAD_EMAIL":
        emails = EMAIL_RE.findall(msg)
        if emails:
            name = USER_DATA.get(user_id, {}).get("name", "Customer")
            email = emails[0]
            CRM_DB["leads"].append({"name": name, "email": email})
            USER_STATE[user_id] = None
            USER_DATA[user_id] = {}
            return {"response": f"Thank you, {name}. I have registered `{email}` and our team at {COMPANY_NAME} will contact you shortly."}
        return {"response": "That does not look like a valid email address. Please share your email so our team can contact you."}

    if current_state == "WAITING_FOR_SUPPORT_NAME":
        if len(raw_msg.split()) > 3:
            return {"response": "That seems a bit long. Please share your first name only."}

        USER_DATA[user_id] = {"name": raw_msg.title()}
        USER_STATE[user_id] = "WAITING_FOR_SUPPORT_EMAIL"
        return {"response": f"Thanks, {raw_msg.title()}. What is the **email address** associated with your account?"}

    if current_state == "WAITING_FOR_SUPPORT_EMAIL":
        emails = EMAIL_RE.findall(msg)
        if emails:
            user_info = USER_DATA.get(user_id, {})
            user_info["email"] = emails[0]
            USER_DATA[user_id] = user_info
            USER_STATE[user_id] = "WAITING_FOR_SUPPORT_ISSUE"
            return {"response": "Got it. Please briefly **describe the issue** you are experiencing."}
        return {"response": "Please provide the email associated with your account so I can create your support ticket."}

    if current_state == "WAITING_FOR_SUPPORT_ISSUE":
        name = USER_DATA.get(user_id, {}).get("name", "Customer")
        email = USER_DATA.get(user_id, {}).get("email", "unknown@domain.com")
        ticket_id = f"TICK-{len(CRM_DB['support_tickets']) + 100}"
        CRM_DB["support_tickets"].append(
            {"ticket": ticket_id, "name": name, "email": email, "issue": raw_msg}
        )
        USER_STATE[user_id] = None
        USER_DATA[user_id] = {}
        return {"response": f"All set, {name}. I created support ticket **{ticket_id}** for `{email}`. Our team will review it shortly."}

    if "tick-" in msg:
        ticket_match = TICKET_RE.search(msg)
        if ticket_match:
            ticket_id = ticket_match.group(0).upper()
            found_ticket = next((t for t in CRM_DB["support_tickets"] if t["ticket"] == ticket_id), None)
            if found_ticket:
                return {
                    "response": (
                        f"I found your ticket **{ticket_id}**.\n\n"
                        f"**Customer:** {found_ticket['name']}\n"
                        f"**Issue:** {found_ticket['issue']}\n"
                        "**Status:** In Progress"
                    )
                }
            return {"response": f"I could not find a ticket with the ID **{ticket_id}**. Please check the number and try again."}

    if any(word in msg for word in ["price", "pricing", "cost", "buy", "features", "demo", "sales", "lead"]):
        USER_STATE[user_id] = "WAITING_FOR_LEAD_NAME"
        return {"response": "I would be happy to help. To get started, please tell me your **name**."}

    if any(word in msg for word in ["help", "bug", "broken", "login", "password", "support", "issue", "error"]):
        USER_STATE[user_id] = "WAITING_FOR_SUPPORT_NAME"
        return {"response": "I am sorry you are facing an issue. Let us create a support ticket. First, please tell me your **name**."}

    return welcome_response()


@app.get("/api/admin")
async def get_admin_data():
    return {
        "leads": CRM_DB["leads"],
        "support_tickets": CRM_DB["support_tickets"],
        "stats": {
            "total_leads": len(CRM_DB["leads"]),
            "total_tickets": len(CRM_DB["support_tickets"]),
        },
    }
