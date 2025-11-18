import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

try:
    # If genai has a list_models() helper it will show available models; otherwise inspect the module
    models = getattr(genai, "list_models", None)
    if callable(models):
        for m in genai.list_models():
            print(m)
    else:
        print("No genai.list_models() available; printing genai attributes instead:")
        print([a for a in dir(genai) if not a.startswith("_")])
except Exception as e:
    print("ERROR:", e)
