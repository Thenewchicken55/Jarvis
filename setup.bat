@echo off
title Jarvis Setup
echo === Jarvis Setup ===
echo.

if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt
pip install pyttsx3 SpeechRecognition 2>nul

echo.
echo === Setup complete! ===
echo.
echo Run Jarvis voice assistant: python jarvis.py
echo Run web chat UI:          streamlit run app.py
echo.

pause
