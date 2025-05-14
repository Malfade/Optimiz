@echo off
chcp 65001 >nul
title API Key Tester

echo Запуск тестирования API ключа...
python test_api_key.py
pause 