@echo off
chcp 65001 > nul
title Bolalar Massaji Telegram Boti

echo ====================================================
echo     Bolalar Massaji Telegram Boti Ishga Tushmoqda
echo ====================================================
echo.

set PYTHON_EXE="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

if exist %PYTHON_EXE% (
    %PYTHON_EXE% bot.py
) else (
    python bot.py
)

echo.
echo Bot to'xtadi yoki xatolik yuz berdi.
pause
