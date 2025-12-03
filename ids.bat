@echo off
REM IDS Tool CLI wrapper - runs the intrusion detection system
REM Usage: ids train, ids batch, ids stream, etc.

if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=python"
)

%PY% -m IDS-tool.src.cli %*
