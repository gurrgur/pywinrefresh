@echo off

echo Initializing python venv...

cd /d "%~dp0"
python -m venv _env
call _env\Scripts\activate.bat
python -m pip install -r requirements.txt

echo Done initializing venv _env.
pause