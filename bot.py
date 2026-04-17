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

# ---------------------------------------------------------
# PUBLIC CRM DATABASE (Mock DB)
# ---------------------------------------------------------
CRM_DB = {
    "leads": [],            
    "support_tickets": []   
}

# ---------------------------------------------------------
# STATE MANAGEMENT & MULTI-STEP MEMORY
# ---------------------------------------------------------
USER_STATE = {} 
USER_DATA = {}  

class ChatMessage(BaseModel):
    message: str
    user_id: str

@app.post("/chat")
async def chat_endpoint(payload: ChatMessage):
    raw_msg = payload.message 
    msg = raw_msg.lower()
    user_id = payload.user_id
    
    # ---------------------------------------------------------
    # THE ESCAPE HATCH (Memory Wipe)
    # ---------------------------------------------------------
    msg_words = msg.split()
    
    if any(word in msg_words for word in ["hi", "hello", "hey", "cancel", "menu", "reset", "restart"]) or "start over" in msg:
        USER_STATE[user_id] = None 
        USER_DATA[user_id] = {} 
        return {
            "response": "Hello! Welcome to our website. How can I help you today?\n\n"
                        "You can ask me about:\n"
                        "📊 **Pricing & Features** (Sales)\n"
                        "🛠️ **Technical Issues & Login Help** (Support)\n"
                        "🔍 **Check Ticket Status** (e.g., 'Check TICK-100')"
        }

    current_state = USER_STATE.get(user_id)

    # =========================================================
    # 1. THE SALES FLOW (Name -> Email -> Webhook)
    # =========================================================
    if current_state == "WAITING_FOR_LEAD_NAME":
        if len(raw_msg.split()) > 3:
            return {"response": "That seems a bit long for a name! Could you please just tell me your first name?"}
            
        USER_DATA[user_id] = {"name": raw_msg.title()} 
        USER_STATE[user_id] = "WAITING_FOR_LEAD_EMAIL"
        return {"response": f"Nice to meet you, {raw_msg.title()}! What is the best **email address** to reach you at?"}

    elif current_state == "WAITING_FOR_LEAD_EMAIL":
        emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", msg)
        if emails:
            name = USER_DATA.get(user_id, {}).get("name", "Customer")
            email = emails[0]
            
            # Save to Database
            CRM_DB["leads"].append({"name": name, "email": email})
            
            # Print Webhook Alert in Terminal
            print("\n" + "="*50)
            print("🚀 [WEBHOOK ALERT] NEW LEAD CAPTURED!")
            print(f" ▸ Name:  {name}")
            print(f" ▸ Email: {email}")
            print("Status: 200 OK - Lead successfully generated on our side.")
            print("="*50 + "\n")
            
            USER_STATE[user_id] = None 
            USER_DATA[user_id] = {}
            return {"response": f"Thank you, {name}! I have registered `{email}` as a new lead. Our sales team will reach out with details shortly."}
        else:
            return {"response": "That doesn't look like a valid email address. Please provide your email so our sales team can contact you."}

    # =========================================================
    # 2. THE SUPPORT FLOW (Name -> Email -> Issue)
    # =========================================================
    elif current_state == "WAITING_FOR_SUPPORT_NAME":
        if len(raw_msg.split()) > 3:
            return {"response": "That seems a bit long! Could you please just tell me your first name?"}
            
        USER_DATA[user_id] = {"name": raw_msg.title()}
        USER_STATE[user_id] = "WAITING_FOR_SUPPORT_EMAIL"
        return {"response": f"Thanks, {raw_msg.title()}. What is the **email address** associated with your account?"}

    elif current_state == "WAITING_FOR_SUPPORT_EMAIL":
        emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", msg)
        if emails:
            user_info = USER_DATA.get(user_id, {})
            user_info["email"] = emails[0]
            USER_DATA[user_id] = user_info
            
            USER_STATE[user_id] = "WAITING_FOR_SUPPORT_ISSUE"
            return {"response": "Got it. Finally, please briefly **describe the issue** you are experiencing so our team can help you faster."}
        else:
            return {"response": "Please provide the email associated with your account so I can create your support ticket."}

    elif current_state == "WAITING_FOR_SUPPORT_ISSUE":
        name = USER_DATA.get(user_id, {}).get("name", "Customer")
        email = USER_DATA.get(user_id, {}).get("email", "unknown@domain.com")
        issue_desc = raw_msg 
        
        ticket_id = f"TICK-{len(CRM_DB['support_tickets']) + 100}"
        
        CRM_DB["support_tickets"].append({
            "ticket": ticket_id, 
            "name": name, 
            "email": email, 
            "issue": issue_desc
        })
        
        USER_STATE[user_id] = None 
        USER_DATA[user_id] = {}
        return {"response": f"All set, {name}! I have created a support ticket (**{ticket_id}**) for `{email}` and attached your problem description. Our technical team will review this shortly."}

    # =========================================================
    # INTENT ROUTING (Entry Points & Lookups)
    # =========================================================
    
    # TICKET LOOKUP FEATURE
    elif "tick-" in msg:
        ticket_match = re.search(r"tick-\d+", msg)
        if ticket_match:
            ticket_id = ticket_match.group(0).upper()
            found_ticket = next((t for t in CRM_DB["support_tickets"] if t["ticket"] == ticket_id), None)
            
            if found_ticket:
                return {"response": f"I found your ticket (**{ticket_id}**)! \n\n"
                                    f"👤 **Customer:** {found_ticket['name']}\n"
                                    f"📝 **Issue:** {found_ticket['issue']}\n"
                                    f"⏳ **Status:** In Progress (Under Review)\n\n"
                                    f"Our technical team is currently looking into this for you."}
            else:
                return {"response": f"I couldn't find a ticket with the ID **{ticket_id}**. Are you sure that is the correct number?"}

    elif any(word in msg for word in ["price", "pricing", "cost", "buy", "features", "demo", "sales", "lead"]):
        USER_STATE[user_id] = "WAITING_FOR_LEAD_NAME"
        return {"response": "I'd be happy to help you get set up! To get started, could you please tell me your **name**?"}

    elif any(word in msg for word in ["help", "bug", "broken", "login", "password", "support", "issue", "error"]):
        USER_STATE[user_id] = "WAITING_FOR_SUPPORT_NAME"
        return {"response": "I'm sorry you are experiencing an issue. Let's get a support ticket created for you. First, could you please tell me your **name**?"}

    # =========================================================
    # DEFAULT FALLBACK
    # =========================================================
    else:
        return {
            "response": "Hello! Welcome to our website. How can I help you today?\n\n"
                        "You can ask me about:\n"
                        "📊 **Pricing & Features** (Sales)\n"
                        "🛠️ **Technical Issues & Login Help** (Support)\n"
                        "🔍 **Check Ticket Status** (e.g., 'Check TICK-100')"
        }

# =========================================================
# ADMIN DASHBOARD ENDPOINT
# =========================================================
@app.get("/api/admin")
async def get_admin_data():
    return {
        "leads": CRM_DB["leads"],
        "support_tickets": CRM_DB["support_tickets"],
        "stats": {
            "total_leads": len(CRM_DB["leads"]),
            "total_tickets": len(CRM_DB["support_tickets"])
        }
    }