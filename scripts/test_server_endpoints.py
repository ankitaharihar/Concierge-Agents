from fastapi.testclient import TestClient
import json
import sys

# Ensure repo root is on path
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web import server

client = TestClient(server.app)


def test_health():
    r = client.get('/health')
    print('/health ->', r.status_code, r.json())


def test_root_html():
    r = client.get('/')
    print('/ ->', r.status_code)
    text = r.text
    # Check for the greeting container id
    has_greeting = 'id="agent-greeting"' in text or "id='agent-greeting'" in text
    print('greeting element present:', has_greeting)


def test_api_chat():
    payload = {'message':'hello','user':'test@example.com'}
    r = client.post('/api/chat', json=payload)
    print('/api/chat ->', r.status_code)
    try:
        print('response json:', r.json())
    except Exception as e:
        print('failed to parse json:', e)


if __name__ == '__main__':
    test_health()
    test_root_html()
    test_api_chat()
