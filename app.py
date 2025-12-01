from flask import Flask
from flask_cors import CORS
from flask import request, jsonify, session, g
from pathlib import Path
from dotenv import load_dotenv
from tools import create_task, list_tasks, update_task_status, generate_plan
import json
from flask import request
import sqlite3
import time
from werkzeug.utils import secure_filename
from flask import send_file, abort
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

# Load .env reliably
project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"
if env_path.exists():
    raw = env_path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        env_path.write_bytes(raw.lstrip(b"\xef\xbb\xbf"))
    load_dotenv(env_path, override=True)
else:
    load_dotenv(override=True)

# Import agent AFTER env loaded
from agent import handle_user_message

# Create Flask app with an absolute static folder path so the server
# serves the frontend regardless of current working directory.
app = Flask(
    "chronoken_api",
    static_folder=str(project_root / "web"),
    static_url_path="",
)
# Allow cookies for same-origin sessions in dev; client should use same origin.
CORS(app, supports_credentials=True)

# Secret key for session cookies (use .env SECRET_KEY in production)
import os
app.secret_key = os.environ.get("SECRET_KEY") or "dev-secret-chronoken"
# ==== Print Registered Routes (for debugging) ====
print("\n=== Registered Flask Routes ===")
for rule in app.url_map.iter_rules():
    print(f"{list(rule.methods)} -> {rule.rule}")
print("=== END Routes ===\n")
# ===================================================
from flask import send_from_directory

# Serve index page using the absolute `web` directory next to this file.
WEB_DIR = project_root / "web"

@app.route("/", methods=["GET"])
def index():
    try:
        return send_from_directory(str(WEB_DIR), "index.html")
    except Exception:
        # fallback minimal page while you debug frontend
        return "<h1>ChronoKen</h1><p>Server running. No frontend found in /web.</p>"

@app.route("/health", methods=["GET"])
def health():
    # Quick-path: handle simple commands server-side to reduce latency for common operations
    mlow = user_message.strip().lower()
    # list tasks
    return jsonify({"status": "ok", "service": "ChronoKen"}), 200
@app.route("/api/message", methods=["POST"])
def api_message():
    """Unified API proxy endpoint for the agent.

    Accepts request JSON with any of these fields for the message text:
      - `message`
      - `text`
      - `user`

    Optional `history` key may be provided as a list.

    # create task: expect format 'create task: title=..., deadline=YYYY-MM-DD, hours=2, priority=high'
    Returns JSON with `reply` and `assistant_message` for compatibility.
    """
    data = request.get_json(force=True, silent=True) or {}
    user_message = data.get("message") or data.get("text") or data.get("user") or ""
    history = data.get("history") or []

    if not user_message:
        return jsonify({"error": "missing message body (expected 'message'|'text'|'user')"}), 400

    try:
        reply = handle_user_message(user_message, history)
    except Exception as e:
        return jsonify({"error": "agent failed", "detail": str(e)}), 500

    return jsonify({"reply": reply, "assistant_message": reply})


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Structured chat API used by the dashboard/WS fallback.

    # generate plan: 'plan' or 'generate plan daily_hours=3 num_days=7'
    Returns JSON: { action, params, assistant_message, plan? }
    """
    data = request.get_json(force=True, silent=True) or {}
    user_message = data.get('message') or data.get('text') or ''
    history = data.get('history') or []
    if not user_message:
        return jsonify({'error':'missing message'}), 400
    try:
        # Use the new structured processor in agent.py
        from agent import process_user_message
        res = process_user_message(user_message, history)
        # Keep backward-compatibility: include `reply` key for clients expecting it
        out = dict(res)
        if 'assistant_message' in res and 'reply' not in res:
            out['reply'] = res.get('assistant_message')

        return jsonify(out)
    except Exception as e:
        return jsonify({'error':'agent failed', 'detail': str(e)}), 500


# ---- Simple tasks storage API (file-backed) ----
DATA_DIR = project_root / 'data'
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / 'chronoken.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                password_hash TEXT,
                avatar TEXT,
                calendar_tokens TEXT,
                created_at INTEGER
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                user_email TEXT NOT NULL,
                title TEXT,
                detail TEXT,
                priority TEXT,
                hours REAL,
                status TEXT,
                created_at INTEGER
            )
        ''')

def migrate_from_json():
    # If JSON files exist from previous demo, import their contents once
    users_file = DATA_DIR / 'users.json'
    tasks_file = DATA_DIR / 'tasks.json'
    db = get_db()
    with db:
        if users_file.exists():
            try:
                users = json.loads(users_file.read_text(encoding='utf-8')) or {}
                for email, u in users.items():
                    try:
                        db.execute('INSERT OR IGNORE INTO users (email,name,password_hash,avatar,created_at) VALUES (?,?,?,?,?)',
                                   (email.lower(), u.get('name') or email.split('@')[0], u.get('password_hash'), u.get('avatar'), int(u.get('id') or time.time()*1000)))
                    except Exception:
                        continue
            except Exception:
                pass

# Ensure avatars folder exists
AVATAR_DIR = DATA_DIR / 'avatars'
AVATAR_DIR.mkdir(exist_ok=True)

@app.route('/avatars/<path:filename>')
def serve_avatar(filename):
    # Serve avatar files saved in data/avatars
    safe = secure_filename(filename)
    file_path = AVATAR_DIR / safe
    if not file_path.exists():
        abort(404)
    return send_file(str(file_path))

# Initialize DB and migrate any existing JSON data into SQLite
with app.app_context():
    init_db()
    # Ensure calendar_tokens column exists (SQLite ADD COLUMN is noop if exists)
    try:
        db = get_db()
        cols = [r['name'] for r in db.execute("PRAGMA table_info(users)").fetchall()]
        if 'calendar_tokens' not in cols:
            db.execute('ALTER TABLE users ADD COLUMN calendar_tokens TEXT')
    except Exception:
        pass
    try:
        migrate_from_json()
    except Exception:
        pass
        if tasks_file.exists():
            try:
                tasks_blob = json.loads(tasks_file.read_text(encoding='utf-8')) or {}
                for user_key, tasks in tasks_blob.items():
                    for t in tasks:
                        try:
                            db.execute('INSERT OR IGNORE INTO tasks (id,user_email,title,detail,priority,hours,status,created_at) VALUES (?,?,?,?,?,?,?,?)',
                                       (t.get('id') or int(time.time()*1000), user_key, t.get('title'), t.get('detail'), t.get('priority'), float(t.get('hours') or 1), t.get('status') or 'pending', int(t.get('id') or time.time()*1000)))
                        except Exception:
                            continue
            except Exception:
                pass

from werkzeug.security import generate_password_hash, check_password_hash

def _find_user_by_email(email):
    if not email:
        return None
    db = get_db()
    row = db.execute('SELECT * FROM users WHERE LOWER(email)=LOWER(?)', (email,)).fetchone()
    return dict(row) if row else None

def _user_public(u):
    if not u:
        return None
    out = {k: v for k, v in u.items() if k != 'password_hash'}
    return out

# Google OAuth config (require these in .env)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_OAUTH_REDIRECT = os.environ.get('GOOGLE_OAUTH_REDIRECT') or 'http://127.0.0.1:8000/api/calendar/oauth2callback'
GOOGLE_OAUTH_SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Fallback: attempt to load client secrets JSON if env vars are not set.
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    # common filenames used when downloading OAuth client credentials from Google Cloud
    possible = [project_root / 'client_secret.json', project_root / 'client_secrets.json', project_root / 'credentials.json']
    for p in possible:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding='utf-8'))
                # Look for web or installed client sections
                cfg = data.get('web') or data.get('installed') or data
                cid = cfg.get('client_id')
                csec = cfg.get('client_secret')
                if cid and csec:
                    GOOGLE_CLIENT_ID = GOOGLE_CLIENT_ID or cid
                    GOOGLE_CLIENT_SECRET = GOOGLE_CLIENT_SECRET or csec
                    print(f'Loaded Google OAuth client from {p}')
                    break
        except Exception as e:
            print('Failed to read client secrets from', p, e)

# Debug: print the effective OAuth configuration so developers can verify
print('Google OAuth effective settings:')
print('  GOOGLE_CLIENT_ID =', GOOGLE_CLIENT_ID)
print('  GOOGLE_OAUTH_REDIRECT =', GOOGLE_OAUTH_REDIRECT)


def _save_calendar_tokens_for_user(email, creds: Credentials):
    if not email or not creds:
        return False
    data = {
        'token': creds.token,
        'refresh_token': getattr(creds, 'refresh_token', None),
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': list(creds.scopes) if creds.scopes else GOOGLE_OAUTH_SCOPES,
        'expiry': creds.expiry.timestamp() if getattr(creds, 'expiry', None) else None
    }
    db = get_db()
    with db:
        db.execute('UPDATE users SET calendar_tokens = ? WHERE LOWER(email)=LOWER(?)', (json.dumps(data), email))
    return True


def _load_calendar_credentials_for_user(email):
    if not email:
        return None
    u = _find_user_by_email(email)
    if not u:
        return None
    tok = u.get('calendar_tokens')
    if not tok:
        return None
    try:
        data = json.loads(tok)
        creds = Credentials(
            token=data.get('token'),
            refresh_token=data.get('refresh_token'),
            token_uri=data.get('token_uri'),
            client_id=data.get('client_id') or GOOGLE_CLIENT_ID,
            client_secret=data.get('client_secret') or GOOGLE_CLIENT_SECRET,
            scopes=data.get('scopes') or GOOGLE_OAUTH_SCOPES,
        )
        return creds
    except Exception:
        return None

@app.route('/api/signup', methods=['POST'])
def api_signup():
    body = request.get_json() or {}
    name = body.get('name') or body.get('fullName') or ''
    email = (body.get('email') or '').strip().lower()
    password = body.get('password') or body.get('pass') or ''
    if not email or not password:
        return jsonify({'error':'email and password required'}), 400
    # check existing
    if _find_user_by_email(email):
        return jsonify({'error':'user_exists'}), 409
    db = get_db()
    created_at = int(time.time()*1000)
    pwd_hash = generate_password_hash(password)
    try:
        with db:
            db.execute('INSERT INTO users (email,name,password_hash,avatar,created_at) VALUES (?,?,?,?,?)', (email, name or email.split('@')[0], pwd_hash, None, created_at))
            row = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            user = dict(row) if row else None
    except sqlite3.IntegrityError:
        return jsonify({'error':'user_exists'}), 409
    except Exception as e:
        return jsonify({'error':'failed_to_save', 'detail': str(e)}), 500
    session['user_email'] = email
    # If the user completed OAuth before signing up, link the pending calendar tokens now
    try:
        pending = session.pop('pending_calendar_tokens', None)
        if pending:
            try:
                pdata = json.loads(pending) if isinstance(pending, str) else pending
                creds = Credentials(
                    token=pdata.get('token'),
                    refresh_token=pdata.get('refresh_token'),
                    token_uri=pdata.get('token_uri'),
                    client_id=pdata.get('client_id') or GOOGLE_CLIENT_ID,
                    client_secret=pdata.get('client_secret') or GOOGLE_CLIENT_SECRET,
                    scopes=pdata.get('scopes') or GOOGLE_OAUTH_SCOPES,
                )
                _save_calendar_tokens_for_user(email, creds)
                print('Linked pending calendar tokens to new user', email)
            except Exception as e:
                print('Failed to link pending calendar tokens on signup:', e)
    except Exception:
        pass
    return jsonify({'user': _user_public(user)})

@app.route('/api/login', methods=['POST'])
def api_login():
    body = request.get_json() or {}
    email = (body.get('email') or '').strip().lower()
    password = body.get('password') or ''
    user = _find_user_by_email(email)
    if not user or not check_password_hash(user.get('password_hash',''), password):
        return jsonify({'error':'invalid_credentials'}), 401
    session['user_email'] = email
    # If the user completed OAuth before logging in, attach pending tokens to this account
    try:
        pending = session.pop('pending_calendar_tokens', None)
        if pending:
            try:
                pdata = json.loads(pending) if isinstance(pending, str) else pending
                creds = Credentials(
                    token=pdata.get('token'),
                    refresh_token=pdata.get('refresh_token'),
                    token_uri=pdata.get('token_uri'),
                    client_id=pdata.get('client_id') or GOOGLE_CLIENT_ID,
                    client_secret=pdata.get('client_secret') or GOOGLE_CLIENT_SECRET,
                    scopes=pdata.get('scopes') or GOOGLE_OAUTH_SCOPES,
                )
                _save_calendar_tokens_for_user(email, creds)
                print('Linked pending calendar tokens to user', email)
            except Exception as e:
                print('Failed to link pending calendar tokens on login:', e)
    except Exception:
        pass
    return jsonify({'user': _user_public(user)})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'ok':True})

@app.route('/api/me', methods=['GET'])
def api_me():
    email = session.get('user_email')
    if not email:
        return jsonify({'user': None}), 200
    user = _find_user_by_email(email)
    # If avatar is stored as a filename, turn into a URL
    u = _user_public(user)
    if u and u.get('avatar'):
        a = u.get('avatar')
        # if it's already a full URL, leave it; otherwise prefix with /avatars/
        if not a.startswith('http') and not a.startswith('/avatars'):
            u['avatar'] = '/avatars/' + a
    return jsonify({'user': u})


@app.route('/api/avatar', methods=['POST'])
def api_avatar():
    # Upload/change avatar for the current session user
    email = session.get('user_email')
    if not email:
        return jsonify({'error':'not_authenticated'}), 401
    if 'avatar' not in request.files:
        return jsonify({'error':'missing_file'}), 400
    f = request.files['avatar']
    if f.filename == '':
        return jsonify({'error':'empty_filename'}), 400
    filename = secure_filename(f.filename)
    # build a unique filename using email and timestamp
    ext = Path(filename).suffix or '.png'
    safe_email = secure_filename(email.replace('@','_at_'))
    out_name = f"{safe_email}_{int(time.time()*1000)}{ext}"
    out_path = AVATAR_DIR / out_name
    try:
        f.save(str(out_path))
    except Exception as e:
        return jsonify({'error':'save_failed','detail':str(e)}), 500
    # update user avatar path in DB
    db = get_db()
    with db:
        db.execute('UPDATE users SET avatar = ? WHERE LOWER(email)=LOWER(?)', (out_name, email))
        row = db.execute('SELECT * FROM users WHERE LOWER(email)=LOWER(?)', (email,)).fetchone()
    user = dict(row) if row else None
    u = _user_public(user)
    if u and u.get('avatar'):
        u['avatar'] = '/avatars/' + u['avatar']
    return jsonify({'user': u})


@app.route('/api/log', methods=['POST'])
def api_log():
    """Development-only UI error logger. Accepts JSON {message, stack, url, extra} and appends to data/ui_errors.log"""
    try:
        payload = request.get_json(force=True, silent=True) or {}
    except Exception:
        payload = {}
    entry = {
        'when': int(time.time()*1000),
        'remote': request.remote_addr,
        'payload': payload
    }
    try:
        log_file = DATA_DIR / 'ui_errors.log'
        with open(log_file, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print('failed to write ui error log', e)
    # also print to console for developer visibility
    try:
        print('UI ERROR LOG:', json.dumps(entry))
    except Exception:
        pass
    return jsonify({'ok': True}), 200


@app.route('/api/calendar/oauth_start', methods=['GET'])
def calendar_oauth_start():
    # Start OAuth flow and return auth_url to frontend
    email = session.get('user_email')
    if not email:
        return jsonify({'error':'not_authenticated'}), 401
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({'error':'google_oauth_not_configured'}), 500
    flow = Flow.from_client_config(
        {
            'web': {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token'
            }
        },
        scopes=GOOGLE_OAUTH_SCOPES,
        redirect_uri=GOOGLE_OAUTH_REDIRECT,
    )
    auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    session['calendar_oauth_state'] = state
    # Debug: log the exact auth_url so developers can inspect Google's error page if needed
    try:
        print('Generated Google OAuth auth_url:')
        print(auth_url)
    except Exception:
        pass
    return jsonify({'auth_url': auth_url})


@app.route('/api/calendar/config', methods=['GET'])
def calendar_config():
    """Debug endpoint: returns the effective Google OAuth client_id and redirect URI."""
    cfg = {
        'loaded_client': bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_OAUTH_REDIRECT,
    }
    return jsonify(cfg)


@app.route('/api/calendar/oauth2callback', methods=['GET'])
def calendar_oauth_callback():
    # Exchange code for tokens and store them for the logged-in user
    state = request.args.get('state') or session.get('calendar_oauth_state')
    code = request.args.get('code')
    if not code:
        return '<p>Missing code</p>', 400
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return '<p>Server not configured</p>', 500
    flow = Flow.from_client_config(
        {
            'web': {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token'
            }
        },
        scopes=GOOGLE_OAUTH_SCOPES,
        state=state,
        redirect_uri=GOOGLE_OAUTH_REDIRECT,
    )
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        return f'<p>Token exchange failed: {e}</p>', 500
    creds = flow.credentials
    # require authenticated user in session
    email = session.get('user_email')
    if not email:
        # If user not authenticated, store tokens in session temporarily
        session['pending_calendar_tokens'] = json.dumps({
            'token': creds.token,
            'refresh_token': getattr(creds, 'refresh_token', None),
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes) if creds.scopes else GOOGLE_OAUTH_SCOPES,
        })
        return '<script>window.close();</script><p>Connected — return to app and sign in to finish linking.</p>'
    # Save tokens to DB for this user
    try:
        _save_calendar_tokens_for_user(email, creds)
    except Exception as e:
        return f'<p>Failed to save tokens: {e}</p>', 500
    return '<script>window.close();</script><p>Calendar connected — you can close this window.</p>'


@app.route('/api/calendar/sync-today', methods=['POST'])
def calendar_sync_today():
    # Create events on the user's primary calendar for today's pending tasks
    email = session.get('user_email')
    if not email:
        return jsonify({'error':'not_authenticated'}), 401
    creds = _load_calendar_credentials_for_user(email)
    if not creds:
        return jsonify({'error':'no_calendar_connected'}), 400
    # refresh if needed
    try:
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            # persist refreshed token
            _save_calendar_tokens_for_user(email, creds)
    except Exception as e:
        return jsonify({'error':'token_refresh_failed', 'detail': str(e)}), 500
    # Build service and insert events from user's tasks
    try:
        service = build('calendar', 'v3', credentials=creds, cache_discovery=False)
    except Exception as e:
        return jsonify({'error':'google_client_init_failed', 'detail': str(e)}), 500
    # load user's tasks
    db = get_db()
    rows = db.execute('SELECT * FROM tasks WHERE user_email = ? AND status != ?', (email, 'done')).fetchall()
    tasks = [dict(r) for r in rows]
    from datetime import datetime, timedelta
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    created = 0
    for i, t in enumerate(tasks):
        try:
            start = now + timedelta(hours=i)
            end = start + timedelta(hours=float(t.get('hours') or 1))
            event = {
                'summary': t.get('title') or 'Task',
                'description': t.get('detail') or '',
                'start': {'dateTime': start.isoformat() + 'Z'},
                'end': {'dateTime': end.isoformat() + 'Z'},
            }
            service.events().insert(calendarId='primary', body=event).execute()
            created += 1
        except Exception:
            continue
    return jsonify({'ok': True, 'created': created})


@app.route('/api/calendar/add-event', methods=['POST'])
def calendar_add_event():
    """Add a single event to the user's primary calendar.
    Request JSON: {summary, description, start: ISO8601, end: ISO8601}
    """
    email = session.get('user_email')
    if not email:
        return jsonify({'error': 'not_authenticated'}), 401
    body = request.get_json(force=True, silent=True) or {}
    summary = body.get('summary') or body.get('title') or 'Event'
    description = body.get('description') or body.get('detail') or ''
    start = body.get('start')
    end = body.get('end')
    if not start or not end:
        return jsonify({'error': 'missing_start_or_end'}), 400

    creds = _load_calendar_credentials_for_user(email)
    if not creds:
        return jsonify({'error': 'no_calendar_connected'}), 400
    try:
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            _save_calendar_tokens_for_user(email, creds)
    except Exception as e:
        return jsonify({'error': 'token_refresh_failed', 'detail': str(e)}), 500

    try:
        service = build('calendar', 'v3', credentials=creds, cache_discovery=False)
    except Exception as e:
        return jsonify({'error': 'google_client_init_failed', 'detail': str(e)}), 500

    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start},
        'end': {'dateTime': end},
    }
    try:
        created = service.events().insert(calendarId='primary', body=event).execute()
        return jsonify({'ok': True, 'event': created}), 200
    except Exception as e:
        return jsonify({'error': 'event_create_failed', 'detail': str(e)}), 500

@app.route('/api/tasks', methods=['GET', 'POST'])
def api_tasks():
    """GET: /api/tasks?user=USER -> returns list
       POST: {user, title, detail, priority, hours} -> saves task and returns it
    """
    db = get_db()
    if request.method == 'GET':
        # prefer explicit ?user=, else fall back to session user
        user = request.args.get('user') or session.get('user_email')
        # if caller passed user=me, interpret as session user
        if user == 'me':
            user = session.get('user_email')
        if not user:
            # no user specified and no session — return empty list
            return jsonify({'tasks': []})
        rows = db.execute('SELECT * FROM tasks WHERE user_email = ? ORDER BY created_at DESC', (user,)).fetchall()
        tasks = [dict(r) for r in rows]
        return jsonify({'tasks': tasks})

    # POST
    body = request.get_json() or {}
    user = body.get('user') or session.get('user_email')
    if not user:
        # require login to associate tasks with a user for persistence
        user = 'guest'
    title = body.get('title') or body.get('message') or 'Untitled'
    detail = body.get('detail') or ''
    priority = body.get('priority') or 'medium'
    try:
        hours = float(body.get('hours') or 1)
    except Exception:
        hours = 1
    created_at = int(time.time()*1000)
    with db:
        cur = db.execute('INSERT INTO tasks (user_email,title,detail,priority,hours,status,created_at) VALUES (?,?,?,?,?,?,?)', (user, title, detail, priority, hours, 'pending', created_at))
        task_id = cur.lastrowid
        row = db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    return jsonify({'task': dict(row)})


@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'PATCH'])
def api_update_task(task_id):
    """Update task fields: title, detail, priority, hours, status
    Returns updated task or 404.
    """
    db = get_db()
    body = request.get_json() or {}
    # Build update set
    allowed = ['title', 'detail', 'priority', 'hours', 'status']
    updates = {}
    for k in allowed:
        if k in body:
            updates[k] = body[k]
    if not updates:
        return jsonify({'error':'no_fields'}), 400
    # Prepare SQL
    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
    params = list(updates.values())
    params.append(task_id)
    try:
        with db:
            db.execute(f'UPDATE tasks SET {set_clause} WHERE id = ?', params)
            row = db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        if not row:
            return jsonify({'error':'not_found'}), 404
        return jsonify({'task': dict(row)})
    except Exception as e:
        return jsonify({'error':'update_failed', 'detail': str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
