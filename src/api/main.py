# src/api/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from src.api.router import router

app = FastAPI(
    title="Financial AI Reasoning Engine",
    description="Full pipeline: Ingestion -> Cleaning -> Reasoning -> Visualization",
    version="1.0"
)

# ==========================================
# 📂 DIRECTORY AUTO-CREATION
# ==========================================
# This prevents RuntimeErrors when saving files or charts
REQUIRED_DIRS = ["data/uploads", "data/static", "data/user-sessions"]

for dir_name in REQUIRED_DIRS:
    path = Path(dir_name)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_name}")

# ==========================================
# 🖼️ STATIC MOUNTING
# ==========================================
# Enables the frontend to view charts at http://127.0.0.1:8000/static/filename.png
app.mount("/static", StaticFiles(directory="data/static"), name="static")

# ==========================================
# 🚀 ROUTER INCLUSION
# ==========================================
# This brings back /upload, /query, and any other routes
app.include_router(router)

@app.get("/")
async def health_check():
    return {
        "status": "online", 
        "engine": "Deterministic Financial Reasoning",
        "directories": "verified"
    }