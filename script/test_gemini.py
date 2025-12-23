# test_gemini.py
import os
from dotenv import load_dotenv
load_dotenv()

print("GEMINI_API_KEY:", os.getenv("GEMINI_API_KEY"))

import google.genai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.0-flash-exp")
response = model.generate_content("Say 'working' if you can read this")
print("Gemini response:", response.text)