# test_gemini.py
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say hello"
    )
    print("SUCCESS:", resp.text)
except Exception as e:
    print("ERROR:", e)