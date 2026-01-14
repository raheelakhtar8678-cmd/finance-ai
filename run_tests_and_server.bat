@echo off
REM Run tests and start FastAPI server with venv environment

echo ============================================================
echo FINANCE-AI: Running Tests and Starting Server
echo ============================================================

REM Activate venv environment
call e:\finance-ai\venv\Scripts\activate.bat

echo.
echo ==================== TEST 1: Instruction Parser ====================
python test\test_instruction_parser.py
echo.

echo ==================== TEST 2: Full Stack Test ====================
python test\test_full_stack.py
echo.

echo ==================== STARTING FASTAPI SERVER ====================
echo Server will be available at:
echo   - API: http://127.0.0.1:8000
echo   - Docs: http://127.0.0.1:8000/docs
echo   - UI: http://127.0.0.1:8000/ui
echo.
echo Press Ctrl+C to stop the server
echo.
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
