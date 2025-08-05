@echo off
:: Change to the parent directory (project root)
cd /d "%~dp0\.."
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo ✅ Setup complete.