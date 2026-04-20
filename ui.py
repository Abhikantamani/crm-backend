from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow your Vercel frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# THIS IS THE FIX FOR THE 422 ERROR
# It strictly tells FastAPI to expect JSON looking like: {"text": "hello"}
class UserMessage(BaseModel):
    text: str

SYSTEM_PROMPT = """
You are a highly professional sales assistant for our CRM platform. 
Answer user questions concisely and accurately.

Here is our company pricing data:
- Setup Fee: $100 one-time fee
- Basic Monthly: $15/month
- Pro API Access: $49/month

CRITICAL RULE: If the user asks about pricing, cost, plans, or fees, you must give a brief 1-sentence summary of our flexibility, and you MUST include the exact text [SHOW_PRICING] at the very end of your response.
"""

@app.post("/chat")
async def chat_endpoint(message: UserMessage):
    user_text = message.text.lower()
    
    # 1. NEW FEATURE: Pricing UI Trigger
    if any(word in user_text for word in ["price", "pricing", "cost", "plan"]):
        return {"reply": "We have a few flexible plans to fit your needs! [SHOW_PRICING]"}
    
    # 2. RESTORED FEATURE: Bug Reporting
    elif any(word in user_text for word in ["bug", "error", "issue", "broken"]):
        return {"reply": "I'm sorry to hear you found a bug. Please describe the issue, or type 'report' to open a ticket."}
    
    # 3. RESTORED FEATURE: Demo Requests
    elif "demo" in user_text:
        return {"reply": "I'd love to show you a demo! You can book a live session here: [DEMO_LINK_STUB] or ask me about specific features."}
    
    # 4. RESTORED FEATURE: Customer Support
    elif "support" in user_text or "help" in user_text:
        return {"reply": "Our support team is available 24/7. Would you like to see our FAQ or speak to a human?"}
    
    # 5. GENERAL FALLBACK
    else:
        return {"reply": f"I received your message: '{message.text}'. How can I assist you with our CRM features, pricing, or bug reporting today?"}