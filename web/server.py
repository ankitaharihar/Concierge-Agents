import os
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Response, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Try to import agent
try:
    from agent import handle_user_message
    AGENT_AVAILABLE = True
except Exception as e:
    print(f"Warning: could not import agent.handle_user_message: {e}")
    AGENT_AVAILABLE = False

# Try to import Google OAuth / API libraries
try:
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GoogleRequest
    GOOGLE_LIBS_AVAILABLE = True
except Exception:
    GOOGLE_LIBS_AVAILABLE = False

# Optional encryption for credentials at rest. Provide a base64 Fernet key
# via the env var `CREDENTIALS_ENCRYPTION_KEY` (urlsafe base64 32-byte key).
try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_AVAILABLE = True
except Exception:
    CRYPTO_AVAILABLE = False

# In-memory store for Flow objects (state->Flow). Credentials persisted to disk in web/credentials.json
FLOW_STORE = {}

def load_all_creds():
    try:
        if CREDS_PATH.exists():
            raw = CREDS_PATH.read_bytes()
            key = os.environ.get('CREDENTIALS_ENCRYPTION_KEY')
            if key and CRYPTO_AVAILABLE:
                try:
                    f = Fernet(key.encode())
                    raw = f.decrypt(raw)
                except InvalidToken:
                    print('Warning: invalid encryption key for credentials file; cannot decrypt')
                    return {}
            # raw now bytes of JSON
            return json.loads(raw.decode('utf-8'))
    except Exception:
        pass
    return {}

def save_all_creds(data: dict):
    try:
        raw = json.dumps(data, indent=2).encode('utf-8')
        key = os.environ.get('CREDENTIALS_ENCRYPTION_KEY')
        if key and CRYPTO_AVAILABLE:
            try:
                f = Fernet(key.encode())
                raw = f.encrypt(raw)
            except Exception as e:
                print(f'Warning: failed to encrypt credentials: {e}')
        CREDS_PATH.write_bytes(raw)
    except Exception as e:
        print(f"Warning: failed to write credentials file: {e}")

def save_creds_for(email: str, creds_json: str):
    d = load_all_creds()
    d[email] = creds_json
    save_all_creds(d)

def get_creds_for(email: str):
    d = load_all_creds()
    return d.get(email)

def remove_creds_for(email: str):
    d = load_all_creds()
    if email in d:
        d.pop(email)
        save_all_creds(d)


def load_creds_object(email: str):
    """Return a google.oauth2.credentials.Credentials object for the email, refreshing if needed."""
    if not GOOGLE_LIBS_AVAILABLE:
        return None
    json_str = get_creds_for(email)
    if not json_str:
        return None
    try:
        info = json.loads(json_str)
        creds = Credentials.from_authorized_user_info(info)
        # Refresh if expired and refresh_token available
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            # persist refreshed creds
            save_creds_for(email, creds.to_json())
        return creds
    except Exception as e:
        print(f"Warning: failed to load creds for {email}: {e}")
        return None

app = FastAPI()

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_ROOT = Path(__file__).parent
# Serve static assets at /static to avoid catching websocket scopes
app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")


@app.get('/')
async def root_index():
    idx = WEB_ROOT / 'index.html'
    if idx.exists():
        return FileResponse(idx)
    return HTMLResponse('<h1>Index not found</h1>', status_code=404)

# Path to persisted credentials (email -> serialized credentials json)
CREDS_PATH = WEB_ROOT / 'credentials.json'

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.post('/api/chat')
async def api_chat(req: Request):
    data = await req.json()
    message = data.get('message')
    user = data.get('user')
    if not message:
        return JSONResponse({'error': 'message required'}, status_code=400)

    if not AGENT_AVAILABLE:
        return {'reply': f'(agent missing) Echo: {message}'}

    # Call the agent synchronously in a thread
    try:
        loop = asyncio.get_running_loop()
        reply = await loop.run_in_executor(None, handle_user_message, message, [])
        return {'reply': reply}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


# --- SendGrid welcome email endpoint ---
def _sendgrid_send(to_email: str, subject: str, html_body: str):
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        raise RuntimeError('SENDGRID_API_KEY not set')
    from requests import post
    from json import dumps
    from_email = os.environ.get('EMAIL_FROM', 'no-reply@chronoken.com')
    payload = {
        'personalizations': [{'to': [{'email': to_email}]}],
        'from': {'email': from_email},
        'subject': subject,
        'content': [{'type': 'text/html', 'value': html_body}]
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    resp = post('https://api.sendgrid.com/v3/mail/send', headers=headers, data=dumps(payload), timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f'SendGrid error {resp.status_code}: {resp.text}')


def _smtp_send(to_email: str, subject: str, html_body: str):
    """Send via SMTP. Uses env vars SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_TLS.
    If none configured, defaults to localhost:1025 (debugging server).
    """
    smtp_host = os.environ.get('SMTP_HOST', 'localhost')
    smtp_port = int(os.environ.get('SMTP_PORT', '1025'))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    use_tls = os.environ.get('SMTP_TLS', 'false').lower() in ('1','true','yes')

    from email.message import EmailMessage
    import smtplib

    msg = EmailMessage()
    from_email = os.environ.get('EMAIL_FROM', 'no-reply@chronoken.com')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    msg.set_content(html_body, subtype='html')

    if smtp_user and smtp_pass:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        try:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        finally:
            server.quit()
    else:
        # No auth configured — attempt to send to a local debug SMTP server
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        try:
            server.send_message(msg)
        finally:
            server.quit()


@app.post('/api/send_welcome')
async def api_send_welcome(req: Request, background_tasks: BackgroundTasks):
    data = await req.json()
    email = data.get('email')
    name = data.get('name') or ''
    if not email:
        return JSONResponse({'error': 'email required'}, status_code=400)
    subject = 'Thanks for visiting ChronoKen'
    html = f"""
    <div style='font-family: Inter, system-ui, Arial; color:#111;'>
      <h3>Thanks for visiting ChronoKen{', '+name if name else ''}!</h3>
      <p>We're glad you stopped by. This is a demo welcome email — replace with your production content.</p>
      <p>— ChronoKen team</p>
    </div>
    """
    try:
        # Prefer SendGrid if configured, otherwise use SMTP fallback (useful for local dev)
        if os.environ.get('SENDGRID_API_KEY'):
            background_tasks.add_task(_sendgrid_send, email, subject, html)
        else:
            background_tasks.add_task(_smtp_send, email, subject, html)
        return {'ok': True}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


    @app.post('/api/generate_timetable')
    async def api_generate_timetable(req: Request):
        """Generate a simple timetable/plan using the server-side planner (tools.generate_plan).
        Accepts JSON: {daily_hours: number, num_days: int}
        """
        data = await req.json()
        try:
            daily_hours = float(data.get('daily_hours', 3.0))
        except Exception:
            daily_hours = 3.0
        try:
            num_days = int(data.get('num_days', 7))
        except Exception:
            num_days = 7

        try:
            plan = generate_plan(daily_hours=daily_hours, num_days=num_days)
            return {'ok': True, 'plan': plan}
        except Exception as e:
            return JSONResponse({'error': str(e)}, status_code=500)

# Simple WebSocket chat endpoint that replies with a single reply per incoming message
@app.websocket('/ws/chat')
async def websocket_chat(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {'message': raw}

            message = payload.get('message')
            if not message:
                await ws.send_text(json.dumps({'error':'message required'}))
                continue

            if not AGENT_AVAILABLE:
                await ws.send_text(json.dumps({'reply': f'(agent missing) Echo: {message}'}))
                continue

            # call agent in thread so we don't block the event loop
            loop = asyncio.get_running_loop()
            try:
                # run the full reply in a thread then stream it in chunks to simulate streaming
                reply = await loop.run_in_executor(None, handle_user_message, message, [])
                # stream in small chunks to give frontend a progressive feel
                chunk_size = 60
                for i in range(0, len(reply), chunk_size):
                    part = reply[i:i+chunk_size]
                    await ws.send_text(json.dumps({'partial': part}))
                    await asyncio.sleep(0.02)
                # final marker
                await ws.send_text(json.dumps({'reply': reply}))
            except Exception as e:
                await ws.send_text(json.dumps({'error': str(e)}))
    except WebSocketDisconnect:
        return


# --- Google OAuth endpoints (server-side) ---
def get_client_secrets_path():
    return os.environ.get('GOOGLE_OAUTH_CLIENT_SECRETS', str(WEB_ROOT / 'client_secret.json'))


@app.get('/auth/google')
async def auth_google():
    if not GOOGLE_LIBS_AVAILABLE:
        return HTMLResponse('<h3>Google libraries not installed.</h3><p>Install google-auth-oauthlib and google-api-python-client in the environment.</p>', status_code=501)

    client_secrets = get_client_secrets_path()
    if not os.path.exists(client_secrets):
        return HTMLResponse(f'<h3>OAuth client secrets not found</h3><p>Expected: {client_secrets}</p>', status_code=400)

    # Create the OAuth flow
    scopes = [
        'https://www.googleapis.com/auth/gmail.send',
        'openid', 'email', 'profile'
    ]
    redirect_uri = f"{os.environ.get('PUBLIC_BASE','http://localhost:8501')}/auth/google/callback"
    flow = Flow.from_client_secrets_file(client_secrets, scopes=scopes, redirect_uri=redirect_uri)

    auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    # store the flow in memory keyed by state for the callback
    FLOW_STORE[state] = flow
    return RedirectResponse(auth_url)


@app.get('/auth/google/callback')
async def auth_google_callback(request: Request):
    if not GOOGLE_LIBS_AVAILABLE:
        return HTMLResponse('<h3>Google libraries not installed.</h3>', status_code=501)

    state = request.query_params.get('state')
    if not state:
        return HTMLResponse('<h3>Missing state in callback</h3>', status_code=400)

    flow = FLOW_STORE.pop(state, None)
    if not flow:
        return HTMLResponse('<h3>OAuth flow not found or expired</h3>', status_code=400)

    # Fetch token using the full callback URL
    full_url = str(request.url)
    try:
        flow.fetch_token(authorization_response=full_url)
        creds = flow.credentials
    except Exception as e:
        return HTMLResponse(f'<h3>Failed to fetch token</h3><pre>{e}</pre>', status_code=500)

    # Get email address via Gmail profile
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress')
    except Exception as e:
        return HTMLResponse(f'<h3>Failed to get Gmail profile</h3><pre>{e}</pre>', status_code=500)

    # Persist serialized credentials to disk (demo only)
    try:
        save_creds_for(email_address, creds.to_json())
    except Exception:
        save_creds_for(email_address, None)

    # Send a login notification email
    try:
        send_login_email(creds, email_address)
        body = f'<h3>Signed in as {email_address}</h3><p>A notification email was sent to your inbox. <a href="/">Return</a></p>'
    except Exception as e:
        body = f'<h3>Signed in as {email_address}</h3><p>But failed to send notification email: {e}</p><p><a href="/">Return</a></p>'

    return HTMLResponse(body)


def send_login_email(credentials, to_email: str):
    # send a simple notification email via Gmail API
    from email.message import EmailMessage
    import base64

    if not GOOGLE_LIBS_AVAILABLE:
        raise RuntimeError('Google libraries missing')

    service = build('gmail', 'v1', credentials=credentials)
    msg = EmailMessage()
    msg['To'] = to_email
    msg['From'] = to_email
    msg['Subject'] = 'Concierge Agent — Successful login'
    msg.set_content(f"Hello {to_email},\n\nYou have successfully logged in to Concierge Agent. If this wasn't you, revoke access in your Google account settings.\n\nRegards,\nConcierge Agent")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = {'raw': raw}
    service.users().messages().send(userId='me', body=body).execute()


@app.get('/auth/status')
async def auth_status():
    # Return list of emails for which we have stored credentials
    creds_map = load_all_creds()
    emails = [k for k, v in creds_map.items() if v]
    return {'accounts': emails}


@app.post('/auth/revoke')
async def auth_revoke(req: Request):
    data = await req.json()
    email = data.get('email')
    if not email:
        return JSONResponse({'error':'email required'}, status_code=400)
    creds = load_creds_object(email)
    if not creds:
        remove_creds_for(email)
        return {'status': 'removed'}

    # revoke via Google's token revocation endpoint
    try:
        import requests
        token = creds.token
        resp = requests.post('https://oauth2.googleapis.com/revoke', params={'token': token}, headers={'content-type':'application/x-www-form-urlencoded'})
        remove_creds_for(email)
        return {'status': 'revoked', 'code': resp.status_code}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/auth/signout')
async def auth_signout(req: Request):
    data = await req.json()
    email = data.get('email')
    if not email:
        return JSONResponse({'error':'email required'}, status_code=400)
    remove_creds_for(email)
    return {'status': 'signed_out'}

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('WEB_PORT', 8501))
    uvicorn.run('web.server:app', host='0.0.0.0', port=port, reload=True)
