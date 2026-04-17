import streamlit as st
import requests

st.set_page_config(page_title="Enterprise CRM Bot", layout="wide")

# 1. Sidebar - This makes it look like a "Complete CRM Setup"
st.sidebar.title("📊 CRM Dashboard")
try:
    stats = requests.get("http://127.0.0.1:8000/crm/summary").json()
    st.sidebar.metric("Active Leads", stats["active_leads"])
    st.sidebar.metric("Open Tickets", stats["open_tickets"])
    st.sidebar.metric("Pipeline Value", stats["revenue_pipeline"])
except:
    st.sidebar.error("Backend Offline")

st.sidebar.markdown("---")
st.sidebar.write("**Current User:** Abhiram (Admin)")

# 2. Main Chat Interface
st.title("🤖 CRM AI Assistant")
st.caption("Connected to Project API v2.0 (Mock Mode Active)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about leads, tickets, or log an issue..."):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # API Call to your FastAPI backend
    try:
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json={"message": prompt},
            headers={"Authorization": "Bearer DEMO_TOKEN_123"}
        )
        full_response = response.json()["response"]
    except:
        full_response = "Error: Backend is not responding. Ensure uvicorn is running on Port 8000."

    # Add bot response to UI
    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})