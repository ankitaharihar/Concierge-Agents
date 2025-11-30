import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# load .env
env_path = Path(__file__).resolve().parent / ".env"
print("ENV PATH:", env_path)
load_dotenv(env_path)

key = os.getenv("GOOGLE_API_KEY")
print("Loaded KEY prefix:", (key[:10] + "...") if key else "None")

if not key:
    raise RuntimeError("GOOGLE_API_KEY not set in environment or .env")

genai.configure(api_key=key)

print("\nFetching available models...\n")
models = genai.list_models()

for m in models:
    name = getattr(m, "name", getattr(m, "model", str(m)))
    methods = getattr(m, "supported_methods", getattr(m, "methods", None))
    print("-----")
    print("name:", name)
    print("methods:", methods)
