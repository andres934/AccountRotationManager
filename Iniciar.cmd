@echo off
cd /d "%~dp0"
echo Abre http://127.0.0.1:8765 en el navegador.
python -B app.py
pause
