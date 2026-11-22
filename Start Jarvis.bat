@echo off
title JARVIS 3.0
cd /d C:\AI-Assistent
python "%~dp0jarvis_app.py"
if errorlevel 1 pause
