@echo off
REM Fast launcher: no environment creation, no pip install and no npm install.
REM First build the React frontend once with: cd frontend && npm run build
call "%~dp0RUN_FAST.bat"
