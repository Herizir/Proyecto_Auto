@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Preparando el entorno por primera vez...
  py -m venv .venv || goto :error
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)
start "" http://127.0.0.1:5000
".venv\Scripts\python.exe" servidor\app.py
pause
exit /b

:error
echo No se pudo preparar el entorno. Revisa que Python este instalado.
pause
