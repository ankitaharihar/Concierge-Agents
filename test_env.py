# test_env.py
from pathlib import Path
from dotenv import load_dotenv
import os

env_path = Path(__file__).resolve().parent / ".env"
print("ENV PATH:", env_path)
print("Exists:", env_path.exists())

if env_path.exists():
    print("\nRaw .env preview:")
    print(env_path.read_text(encoding='utf-8', errors='replace'))

# Load env
load_dotenv(env_path)

print("\nAfter load:")
print("GOOGLE_API_KEY prefix:", (os.getenv("GOOGLE_API_KEY") or "None")[:12] + "...")
print("MODEL_NAME:", os.getenv("MODEL_NAME"))
