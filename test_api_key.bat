@echo off
chcp 65001 >nul
title API Key Tester

echo Тестирование API ключа...
python test_api_key.py
pause 