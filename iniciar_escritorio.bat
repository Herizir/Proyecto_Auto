@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Preparando el entorno por primera vez...
  py -m venv .venv || goto :error
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)
start "" ".venv\Scripts\pythonw.exe" escritorio\app.py
exit /b

:error
echo No se pudo preparar el entorno. Revisa que Python este instalado.
pause
