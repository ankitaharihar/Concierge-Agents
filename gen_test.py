# gen_test.py - explicit dotenv + direct configure
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"
print('Looking for .env at:', env_path)
if env_path.exists():
    raw = env_path.read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'):
        env_path.write_bytes(raw.lstrip(b'\xef\xbb\xbf'))
    load_dotenv(env_path)
else:
    print('.env not found; will rely on environment variables.')

api_key = os.getenv('GOOGLE_API_KEY')
model_name = os.getenv('MODEL_NAME')
print('GOOGLE_API_KEY prefix:', (api_key[:12] + '...') if api_key else 'None...')
print('MODEL_NAME:', model_name)

if not api_key:
    raise SystemExit('ERROR: GOOGLE_API_KEY not found in environment or .env. Set it and re-run.')

genai.configure(api_key=api_key)
model_to_use = model_name or 'models/gemini-2.5-pro'
print('Using model:', model_to_use)

model = genai.GenerativeModel(model_to_use)
resp = model.generate_content('ChronoKen quick test: say Hello in one sentence.')
print('RESPONSE PREVIEW:', getattr(resp, 'text', None) or str(resp)[:400])
