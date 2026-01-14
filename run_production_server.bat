@echo off
REM Production server with multi-worker setup for higher concurrency
REM Capacity: 30-50 concurrent users (vs 3-5 with single worker)

echo ============================================================
echo FINANCE-AI: PRODUCTION SERVER (Multi-Worker Mode)
echo ============================================================
echo.
echo CAPACITY: ~30-50 concurrent users
echo WORKERS: 4 processes
echo.

REM Activate venv environment
call e:\finance-ai\venv\Scripts\activate.bat

echo ==================== PRE-FLIGHT CHECKS ====================
echo Checking dependencies...
python -c "import uvicorn; import fastapi; import chromadb; print('All dependencies OK')"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Missing dependencies. Run: pip install -r requirements.txt
    exit /b 1
)
echo.

echo ==================== STARTING PRODUCTION SERVER ====================
echo.
echo Server will be available at:
echo   - API: http://0.0.0.0:8000
echo   - Docs: http://0.0.0.0:8000/docs
echo   - UI: http://0.0.0.0:8000/ui
echo.
echo Workers: 4 parallel processes
echo Timeout: 120 seconds per request
echo.
echo Press Ctrl+C to stop the server
echo.

REM Production settings:
REM   --workers 4          : 4 parallel worker processes
REM   --timeout-keep-alive 120 : Keep connections alive for 2 min
REM   --limit-concurrency 50   : Max concurrent connections per worker
REM   --log-level info     : Reduce log verbosity
REM   NO --reload          : Disabled for production (faster startup)

python -m uvicorn src.api.main:app ^
    --host 0.0.0.0 ^
    --port 8000 ^
    --workers 4 ^
    --timeout-keep-alive 120 ^
    --limit-concurrency 50 ^
    --log-level info
