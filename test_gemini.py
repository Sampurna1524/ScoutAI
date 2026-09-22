import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise EnvironmentError(
        "Missing GEMINI_API_KEY or GOOGLE_API_KEY environment variable. "
        "Set it in backend/.env or the process environment."
    )

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Say hello in one sentence."
)

print(response.text)