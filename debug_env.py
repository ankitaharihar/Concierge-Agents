# debug_env.py — deep debug for .env parsing
from pathlib import Path
from dotenv import load_dotenv
import os, sys, codecs

env_path = Path(__file__).resolve().parent / ".env"
print("ENV PATH:", env_path)
print("Exists:", env_path.exists())
if not env_path.exists():
    sys.exit("NO .env")

# read raw bytes and show repr to reveal hidden chars
raw_bytes = env_path.read_bytes()
try:
    raw_text = raw_bytes.decode("utf-8")
except Exception as e:
    raw_text = raw_bytes.decode("utf-8", errors="replace")
print("\\n-- RAW BYTES (first 200 bytes) repr() --")
print(repr(raw_bytes[:200]))
print("\\n-- RAW TEXT (first 10 lines with repr) --")
for i, ln in enumerate(raw_text.splitlines()):
    print(f"{i+1}: {repr(ln)}")
    if i >= 9:
        break

# Try loading WITHOUT override, show return value and env var
r = load_dotenv(env_path, override=False)
print("\\nload_dotenv returned (override=False):", r)
print("os.environ contains keys related to GOOGLE_API_KEY:", any(k.upper().startswith("GOOGLE_API_KEY") for k in os.environ.keys()))
print("os.getenv('GOOGLE_API_KEY') ->", repr(os.getenv("GOOGLE_API_KEY")))

# Now force load with override=True
r2 = load_dotenv(env_path, override=True)
print("\\nload_dotenv returned (override=True):", r2)
print("After override load, os.getenv('GOOGLE_API_KEY') ->", repr(os.getenv("GOOGLE_API_KEY")))

# Show exact keys that contain 'GOOGLE' to spot trimmed/hidden names
print("\\nKeys containing 'GOOGLE' (showing repr):")
for k in sorted(os.environ.keys()):
    if "GOOGLE" in k.upper():
        print(repr(k), "->", repr(os.environ.get(k)))
