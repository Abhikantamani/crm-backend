from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# import your AI libraries here (e.g., openai, google.generativeai, etc.)

app = FastAPI()

# 🚨 REQUIRED FOR VERCEL TO TALK TO RENDER
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you can replace "*" with your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserMessage(BaseModel):
    text: str

# 1. Your System Prompt / Data Dump
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
    user_text = message.text
    
    # ---------------------------------------------------------
    # 2. YOUR AI LOGIC GOES HERE
    # Connect to your LLM (LLAMA, OpenAI, Gemini, etc.) and pass 
    # both the SYSTEM_PROMPT and the user_text.
    #
    # Example placeholder logic if you don't have the AI hooked up yet:
    # ---------------------------------------------------------
    
    user_text_lower = user_text.lower()
    if "price" in user_text_lower or "cost" in user_text_lower or "plan" in user_text_lower:
        ai_response = "We have a few flexible plans to fit your needs! [SHOW_PRICING]"
    else:
        ai_response = f"You said: {user_text}. I am a CRM bot, how can I help you today?"

    # Return the response to the React frontend
    return {"reply": ai_response}