import streamlit as st  # type: ignore[reportMissingImports]
from dotenv import load_dotenv
import os

load_dotenv()

# Import the project's agent function and storage helpers
from agent import handle_user_message
from storage import load_tasks, save_tasks, get_next_task_id

import json
import base64
from email.message import EmailMessage
import hashlib
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_LIBS_AVAILABLE = True
except Exception:
    GOOGLE_LIBS_AVAILABLE = False


st.set_page_config(page_title="Concierge Agent", layout="wide")

# Initialize per-user conversation histories and current user
if "histories" not in st.session_state:
    st.session_state.histories = {}
if "user" not in st.session_state:
    st.session_state.user = None


def login_page():
    # Two-column hero + card layout to match the example design
    st.markdown("""
    <style>
    /* Full-page purple background */
    .stApp > main {background: linear-gradient(180deg, #5b26b6 0%, #2f2fa3 60%);}

    /* Layout */
    .hero {display:flex;gap:48px;padding:56px 64px;height:720px;align-items:center}
    .left {flex:1;color:#fff;padding:60px;border-radius:12px;background:transparent}
    .right {width:520px}

    /* Card */
    .card {background:#fbf9ff;border-radius:18px;padding:32px;box-shadow:0 20px 60px rgba(12,10,30,0.45);border:1px solid rgba(255,255,255,0.06)}
    .card h2{margin:0 0 6px 0}
    .small-muted{color:#78818a;font-size:14px;margin-bottom:8px}

    /* Google button styling (target only first .stButton inside the card) */
    .card .stButton>button {display:flex;align-items:center;gap:10px;border-radius:10px;padding:10px 16px;font-size:15px;border:1px solid rgba(20,20,24,0.06);background:#fff}
    .card .stButton>button svg {height:18px;width:18px}

    /* Primary sign-in button (purple) - target form submit button only */
    .card form .stButton>button{background:linear-gradient(90deg,#6b46ff,#6246ff);color:#fff;border:none;padding:12px 18px;border-radius:10px;font-weight:700}
    .card form .stButton>button:hover{filter:brightness(1.03)}

    /* Form fields */
    .stTextInput>div>div>input {height:48px !important;padding:12px 14px;border-radius:10px;background:#f4f5fb}
    .stCheckbox>div>div{align-items:center}

    /* Feature boxes left */
    .feature {background:rgba(255,255,255,0.06);padding:18px;border-radius:12px;margin-bottom:14px}
    .feature strong{display:block;font-size:16px;margin-bottom:6px}
    .feature p{margin:0;color:rgba(255,255,255,0.9)}

    /* Responsive */
    @media(max-width:1000px){.hero{flex-direction:column;padding:20px;height:auto}.right{width:100%}}
    </style>
    """, unsafe_allow_html=True)

    left_col, right_col = st.columns([2, 1])
    with left_col:
        st.markdown("<div class='left'>", unsafe_allow_html=True)
        st.markdown("<h1 style='font-size:48px;margin-bottom:6px'>Plan smarter,<br><span style='opacity:0.95'>achieve more</span></h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:18px;max-width:520px'>Your intelligent task planning assistant that understands your goals and creates personalized plans tailored to your needs.</p>", unsafe_allow_html=True)
        st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
        st.markdown("<div style='background:rgba(255,255,255,0.06);padding:18px;border-radius:12px;margin-bottom:12px'><strong>Smart Task Breakdown</strong><div style='opacity:0.85'>AI automatically breaks down complex goals into manageable steps</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='background:rgba(255,255,255,0.06);padding:18px;border-radius:12px;margin-bottom:12px'><strong>Adaptive Scheduling</strong><div style='opacity:0.85'>Plans that adapt to your pace and priorities in real-time</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='background:rgba(255,255,255,0.06);padding:18px;border-radius:12px'><strong>Personalized Insights</strong><div style='opacity:0.85'>Get intelligent suggestions based on your working style</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("<div class='right'>", unsafe_allow_html=True)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom:6px'>Welcome back</h2>", unsafe_allow_html=True)
        st.markdown("<div class='small-muted'>Sign in to continue planning your success</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # Google sign-in big button
        if GOOGLE_LIBS_AVAILABLE:
            if st.button("\U0001F310  Continue with Google", key="google_sign_in_big"):
                google_login()
        else:
            st.button("\U0001F310  Continue with Google", key="google_sign_in_big_disabled", disabled=True)
            st.info("Google OAuth not available. Install google-auth-oauthlib & google-api-python-client in the environment to enable this.")

            # Diagnostic info to help debug environment issues
            import sys
            client_secrets = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRETS", "client_secret.json")
            with st.expander("Debug: Google OAuth environment info"):
                st.write(f"Google libs installed: {GOOGLE_LIBS_AVAILABLE}")
                st.write(f"Python executable: {sys.executable}")
                st.write(f"client_secret.json present: {os.path.exists(client_secrets)}")
                st.write("If Google libs are missing here, install them into the same Python interpreter listed above and run Streamlit with that interpreter:\n```.venv\\Scripts\\python.exe -m streamlit run ui_streamlit.py```")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;color:#9aa0a6'>or continue with email</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Login form using st.form so the submit button can be styled separately
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            remember = st.checkbox("Remember me", key="remember_me")
            submitted = st.form_submit_button("Sign in")
            if submitted:
                if email and password:
                    if verify_user(email, password):
                        st.session_state.user = email
                        if email not in st.session_state.histories:
                            st.session_state.histories[email] = []
                        st.success("Signed in")
                        st.experimental_rerun()
                    else:
                        st.error("Invalid email or password")
                else:
                    st.error("Email and password required")

        # Forgot password and create account actions
        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("Forgot password?", key="forgot_pw"):
                st.info("Password reset not implemented in this demo.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center'>Don't have an account?</div>", unsafe_allow_html=True)
        if st.button("Create account", key="show_create"):
            st.session_state.show_register = True

        # Show registration when requested
        if st.session_state.get("show_register"):
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("Create account")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            if st.button("Create account", key="create_account"):
                if reg_email and reg_password:
                    if create_user(reg_email, reg_password):
                        st.success("Account created — you can now log in")
                        st.session_state.show_register = False
                    else:
                        st.error("Account already exists")
                else:
                    st.error("Email and password required")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


### Local user store helpers
USERS_FILE = Path("users.json")


def load_users():
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_user(email: str, password: str) -> bool:
    users = load_users()
    entry = users.get(email)
    if not entry:
        return False
    return entry.get("password") == hash_password(password)


def create_user(email: str, password: str) -> bool:
    users = load_users()
    if email in users:
        return False
    users[email] = {"password": hash_password(password)}
    save_users(users)
    return True



def logout():
    st.session_state.user = None
    st.experimental_rerun()


def dashboard_page(username: str):
    st.sidebar.markdown(f"**Signed in as:** {username}")
    if st.sidebar.button("Logout"):
        logout()
        return

    st.title(f"{username}'s Dashboard")
    col1, col2 = st.columns([2, 1])

    # Chat area
    with col1:
        st.header("Chat with the agent")
        history = st.session_state.histories.get(username, [])
        for role, text in history:
            if role == "user":
                st.markdown(f"**You:** {text}")
            else:
                st.markdown(f"**Assistant:** {text}")

        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Message", key=f"msg_{username}")
            submitted = st.form_submit_button("Send")
            if submitted and user_input:
                st.session_state.histories[username].append(("user", user_input))
                try:
                    assistant_reply = handle_user_message(user_input, [])
                except Exception as e:
                    assistant_reply = f"(error calling agent) {e}"
                st.session_state.histories[username].append(("assistant", assistant_reply))
                st.experimental_rerun()

    # Tasks area
    with col2:
        st.header("Tasks")
        tasks = load_tasks()
        # If tasks contain an `owner` field, show only the user's tasks by default
        if tasks and isinstance(tasks, list) and all(isinstance(t, dict) for t in tasks) and any("owner" in t for t in tasks):
            user_tasks = [t for t in tasks if t.get("owner") == username]
        else:
            # no owner field found; show all tasks but allow assign-to-me
            user_tasks = tasks

        if user_tasks:
            for t in user_tasks:
                st.write(f"**{t.get('title','(no title)')}**  — status: {t.get('status','todo')}")
                st.write(f"Due: {t.get('due','n/a')} — id: {t.get('id')}")
                if t.get('owner') != username:
                    if st.button(f"Assign to me: {t.get('id')}"):
                        t['owner'] = username
                        save_tasks(tasks)
                        st.experimental_rerun()
                st.markdown("---")
        else:
            st.info("You have no tasks assigned yet.")

        st.subheader("Add a task")
        with st.form("add_task_form"):
            title = st.text_input("Title")
            due = st.text_input("Due (YYYY-MM-DD)")
            submitted = st.form_submit_button("Add Task")
            if submitted and title:
                tasks = load_tasks()
                new_id = get_next_task_id(tasks)
                new_task = {"id": new_id, "title": title, "due": due, "owner": username, "status": "todo"}
                tasks.append(new_task)
                save_tasks(tasks)
                st.success("Task added")
                st.experimental_rerun()


def main():
    if not st.session_state.user:
        login_page()
    else:
        dashboard_page(st.session_state.user)


def google_login():
    """Run an OAuth local-server flow and store credentials in session state. Sends a login email to the Google account if successful."""
    client_secrets = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRETS", "client_secret.json")
    scopes = [
        "https://www.googleapis.com/auth/gmail.send",
        "openid",
        "email",
        "profile",
    ]

    if not os.path.exists(client_secrets):
        st.error(f"OAuth client secrets file not found: {client_secrets}")
        st.info("Create an OAuth 2.0 Client ID in Google Cloud Console, download the JSON, and set the path in env var GOOGLE_OAUTH_CLIENT_SECRETS or place it as client_secret.json in the repo root.")
        return

    try:
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets, scopes=scopes)
        creds = flow.run_local_server(port=0)

        # get email via Gmail profile
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        email_address = profile.get("emailAddress")

        if email_address:
            # set session user to the Google email
            st.session_state.user = email_address
            if email_address not in st.session_state.histories:
                st.session_state.histories[email_address] = []

            # store credentials json in session (so we can reuse for sending later in this session)
            try:
                st.session_state.google_creds = creds.to_json()
            except Exception:
                # fallback: don't persist creds
                st.session_state.google_creds = None

            # send a login notification email
            try:
                send_login_email(creds, email_address)
                st.success(f"Signed in as {email_address} — notification email sent.")
                # provide a quick link to open Gmail for the signed-in account
                gmail_url = f"https://mail.google.com/mail/u/0/#inbox?authuser={email_address}"
                st.markdown(f"[Open Gmail]({gmail_url})", unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Signed in as {email_address} but failed to send email: {e}")

            st.experimental_rerun()
        else:
            st.error("Failed to determine Google account email after sign-in.")
    except Exception as e:
        st.error(f"Google sign-in failed: {e}")


def send_login_email(credentials, to_email: str):
    """Send a simple login notification email to `to_email` using the Gmail API and provided credentials."""
    if not GOOGLE_LIBS_AVAILABLE:
        raise RuntimeError("Google libraries missing")

    service = build("gmail", "v1", credentials=credentials)

    msg = EmailMessage()
    msg["To"] = to_email
    msg["From"] = to_email
    msg["Subject"] = "Concierge Agent — Successful login"
    msg.set_content(f"Hello {to_email},\n\nYou have successfully logged in to our system (Concierge Agent). If this wasn't you, revoke access in your Google account settings.\n\nRegards,\nConcierge Agent")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = {"raw": raw}
    service.users().messages().send(userId="me", body=body).execute()


if __name__ == "__main__":
    main()
