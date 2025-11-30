from flask import Flask
from flask_cors import CORS
app = Flask(__name__, static_folder="web", static_url_path="/static")  # static_folder optional
CORS(app)
# app.py — lightweight Flask wrapper for ChronoKen
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv

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

app = Flask("chronoken_api")
CORS(app)

# ==== Print Registered Routes (for debugging) ====
print("\n=== Registered Flask Routes ===")
for rule in app.url_map.iter_rules():
    print(f"{list(rule.methods)} -> {rule.rule}")
print("=== END Routes ===\n")
# ===================================================
from flask import send_from_directory, request, jsonify
# Serve index page if you have a frontend under `web/index.html`
@app.route("/", methods=["GET"])
def index():
    try:
        return send_from_directory("web", "index.html")
    except Exception:
        # fallback minimal page while you debug frontend
        return "<h1>ChronoKen</h1><p>Server running. No frontend found in /web.</p>"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "ChronoKen"}), 200

# API proxy endpoint that calls your agent handler
# make sure handle_user_message is imported above: from agent import handle_user_message
@app.route("/api/message", methods=["POST"])
def api_message():
    data = request.get_json(force=True, silent=True) or {}
    user_message = data.get("message") or data.get("text") or ""
    history = data.get("history") or []
    try:
        reply = handle_user_message(user_message, history)
    except Exception as e:
        return jsonify({"error": "agent failed", "detail": str(e)}), 500
    return jsonify({"reply": reply})


@app.route("/api/message", methods=["POST"])
def api_message():
    """
    Request JSON:
    { "user": "message text", "history": [ {"user":"..","assistant":".."}, ... ] }
    Response JSON:
    { "assistant_message": "string" }
    """
    data = request.get_json() or {}
    user = data.get("user", "")
    history = data.get("history", []) or []
    if not user:
        return jsonify({"error": "missing 'user' field"}), 400

    reply = handle_user_message(user, history)
    return jsonify({"assistant_message": reply})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
