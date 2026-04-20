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
    # message.text matches the BaseModel perfectly
    user_text = message.text.lower()
    
    # Simple logic check to trigger the UI component
    if "price" in user_text or "cost" in user_text or "plan" in user_text:
        ai_response = "We have a few flexible plans to fit your needs! [SHOW_PRICING]"
    else:
        # If you have an LLM hooked up, its response would go here instead.
        ai_response = f"You said: '{message.text}'. I am a CRM bot, ask me about our pricing!"

    # Returning exactly what React is looking for (data.reply)
    return {"reply": ai_response}