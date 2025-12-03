@echo off
REM Simple wrapper to run the project CLI: ids <command> [args]
if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=python"
)
%PY% -m src.cli %*
