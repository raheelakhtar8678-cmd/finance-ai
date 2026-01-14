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
# 🚀 ROUTER & UI INCLUSION
# ==========================================
app.include_router(router)

# Mount Gradio UI
try:
    import gradio as gr
    from app import demo
    app = gr.mount_gradio_app(app, demo, path="/ui")
    print("✅ Gradio UI mounted at http://127.0.0.1:8000/ui")
except Exception as e:
    print(f"⚠️ Could not mount Gradio UI: {e}")

@app.get("/")
async def health_check():
    return {
        "status": "online", 
        "engine": "Deterministic Financial Reasoning",
        "ui": "/ui",
        "directories": "verified"
    }