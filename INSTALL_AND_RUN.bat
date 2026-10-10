@echo off
setlocal
cd /d "%~dp0"
echo Installing all Pitchora dependencies, including PDF export support...
python -m pip install --upgrade pip
if errorlevel 1 goto failed
python -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Dependencies installed successfully.
echo Start Pitchora by running: python app.py
echo Then open http://127.0.0.1:5000 in your browser.
pause
exit /b 0
:failed
echo.
echo Installation failed. Check the Python/pip error shown above.
pause
exit /b 1
