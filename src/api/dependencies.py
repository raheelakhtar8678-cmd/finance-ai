# src/api/dependencies.py
import os
from dotenv import load_dotenv

load_dotenv()

def get_gemini_key():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Missing GEMINI_API_KEY")
    return key

def get_openrouter_key():
    return os.getenv("OPENROUTER_API_KEY")