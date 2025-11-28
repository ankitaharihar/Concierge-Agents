Web UI (static) + FastAPI backend for Concierge Agent
Web UI (static) + FastAPI backend for Concierge Agent

Files added under `web/`:
- `index.html` — static HTML UI (hero + right card, Google button, email login, chat view)
- `styles.css` — UI styles matching the screenshot intent
- `app.js` — client JS: tries WebSocket `/ws/chat` first, falls back to REST `/api/chat`
- `server.py` — FastAPI server that serves static files, `/api/chat` REST endpoint and `/ws/chat` WebSocket. It attempts to import `agent.handle_user_message`; if the import fails it returns an echo response so the frontend remains usable.

Quick start (PowerShell, from repo root):

1) Activate your venv (optional, recommended):

```powershell
.\.venv\Scripts\Activate.ps1
```

2) Install server deps (inside the venv):

```powershell
python -m pip install fastapi uvicorn
```

If your venv already contains the project requirements, you're likely ready; otherwise install project deps too.

3) Run the server:

```powershell
python web\server.py
```

Open http://localhost:8501

Notes and next steps:
 - To enable real Google OAuth and Gmail sends, install the Google libraries into your environment and provide a client secrets file:
	 - Install:
		 ```powershell
		 python -m pip install google-auth-oauthlib google-api-python-client
		 ```
	 - Create OAuth 2.0 Client Credentials (Web application) in Google Cloud Console, add an Authorized redirect URI such as `http://localhost:8501/auth/google/callback`, download the JSON and place it at `web/client_secret.json` or set env var `GOOGLE_OAUTH_CLIENT_SECRETS` to its path.
	 - Start the server and visit `/auth/google` to begin sign-in. The server will attempt to send a login notification email after successful sign-in.

 - To enable streaming partial replies, we can extend `/ws/chat` to stream incremental tokens (requires agent support for streaming).

Security note: the OAuth flow and credentials are stored in-memory in this demo (`FLOW_STORE`, `CREDENTIALS_STORE`). For production you must use a secure, persistent credential store and protect client secrets.