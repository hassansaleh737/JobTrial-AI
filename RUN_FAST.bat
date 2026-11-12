@echo off
setlocal
cd /d "%~dp0"
if not exist "frontend\dist\index.html" (
 echo ERROR: Frontend build missing.
 echo Run once: cd frontend ^&^& npm install --include=dev ^&^& npm run build
 echo Then return to this folder and run RUN_FAST.bat again.
 pause
 exit /b 1
)
if not exist ".env" if exist ".env.example" copy /Y ".env.example" ".env" >nul
where python >nul 2>&1
if errorlevel 1 (
 echo ERROR: Python not found in current environment.
 pause
 exit /b 1
)
echo Running JobTrial AI using current Python environment.
echo Open http://127.0.0.1:8000
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
