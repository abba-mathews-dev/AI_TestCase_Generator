@echo off
echo === TestCraft Backend Setup ===

if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
)

echo [2/4] Activating environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install -r requirements.txt -q
python -m spacy download en_core_web_sm -q 2>nul

echo [4/4] Starting server on http://localhost:8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000
