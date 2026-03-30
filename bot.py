import requests
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

class Message(BaseModel):
    message: str

session_state = {}

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

@app.post("/chat")
async def chat_endpoint(user_input: Message):
    user_msg = user_input.message.lower()
    user_id = "user1"

    if user_id not in session_state:
        session_state[user_id] = {"flow": None, "step": 0, "data": {}}

    state = session_state[user_id]

    if state["flow"] is None:
        if "pricing" in user_msg or "buy" in user_msg or "sales" in user_msg:
            state["flow"] = "sales"
            state["step"] = 1
            return {"reply": "Hi! I can help you with sales. What is your name?"}
        elif "bug" in user_msg or "issue" in user_msg or "support" in user_msg:
            state["flow"] = "support"
            state["step"] = 1
            return {"reply": "I can help you with support. What is your email address?"}
        else:
            return {"reply": "Welcome! Are you looking for Sales (pricing) or Support (report an issue)?"}

    if state["flow"] == "sales":
        if state["step"] == 1:
            state["data"]["name"] = user_input.message
            state["step"] = 2
            return {"reply": f"Nice to meet you, {state['data']['name']}! What is your email address?"}
        elif state["step"] == 2:
            if is_valid_email(user_msg):
                state["data"]["email"] = user_msg
                state["step"] = 3
                return {"reply": "Thanks! What are your specific requirements?"}
            else:
                return {"reply": "That doesn't look like a valid email. Could you try again?"}
        elif state["step"] == 3:
            state["data"]["requirement"] = user_input.message
            
            db_url = "https://httpbin.org/post"
            lead_payload = {
                "name": state["data"]["name"],
                "email": state["data"]["email"],
                "phone": "Not provided",
                "status": "New",
                "source": "Chatbot",
                "notes": state["data"]["requirement"]
            }
            
            try:
                requests.post(db_url, json=lead_payload)
                print("SUCCESS: Lead mapped and sent!")
            except Exception as e:
                print(f"ERROR: Failed to send lead. {e}")

            session_state[user_id] = {"flow": None, "step": 0, "data": {}}
            return {"reply": "Got it! I've saved your request and sent it to our sales team."}

    elif state["flow"] == "support":
        if state["step"] == 1:
            if is_valid_email(user_msg):
                state["data"]["email"] = user_msg
                state["step"] = 2
                return {"reply": "Thanks! Please describe the issue you are facing."}
            else:
                return {"reply": "That doesn't look like a valid email. Could you try again?"}
        elif state["step"] == 2:
            state["data"]["issue"] = user_input.message
            
            db_url = "https://httpbin.org/post"
            ticket_payload = {
                "email": state["data"]["email"],
                "subject": "Chatbot Support Request",
                "description": state["data"]["issue"],
                "status": "Open",
                "priority": "Medium"
            }
            
            try:
                requests.post(db_url, json=ticket_payload)
                print("SUCCESS: Ticket mapped and sent!")
            except Exception as e:
                print(f"ERROR: Failed to send ticket. {e}")

            session_state[user_id] = {"flow": None, "step": 0, "data": {}}
            return {"reply": "Got it! I've logged your issue and our support team will look into it."}