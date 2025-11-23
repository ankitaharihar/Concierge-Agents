import streamlit as st  # type: ignore[reportMissingImports]
from dotenv import load_dotenv
import os

load_dotenv()

# Import the project's agent function
from agent import handle_user_message

st.set_page_config(page_title="Concierge Agent", layout="centered")

if "history" not in st.session_state:
    st.session_state.history = []

st.title("Concierge Agent")

st.markdown("Ask the agent anything. Messages are sent to your local agent implementation using the API key in your `.env`.")

for role, text in st.session_state.history:
    if role == "user":
        st.markdown(f"**You:** {text}")
    else:
        st.markdown(f"**Assistant:** {text}")

with st.form("input_form", clear_on_submit=True):
    user_input = st.text_input("Message", "")
    submitted = st.form_submit_button("Send")
    if submitted and user_input:
        st.session_state.history.append(("user", user_input))
        try:
            assistant_reply = handle_user_message(user_input, [])
        except Exception as e:
            assistant_reply = f"(error calling agent) {e}"
        st.session_state.history.append(("assistant", assistant_reply))
