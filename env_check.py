import os
print("PYTHON:", os.sys.executable)
print("GOOGLE_API_KEY prefix:", (os.getenv("GOOGLE_API_KEY") or "None")[:12] + "...")
print("MODEL_NAME:", os.getenv("MODEL_NAME"))
