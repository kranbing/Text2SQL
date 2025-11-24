@echo off
setlocal
set ROOT=%~dp0..
cd /d "%ROOT%"
start "" python -m uvicorn api.main:app --port 8001 --reload
cd /d "%ROOT%\front_end"
start "" python -m http.server 8000
start "" http://127.0.0.1:8000/