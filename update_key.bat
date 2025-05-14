@echo off
chcp 65001 >nul
title API Key Updater

echo Запуск утилиты обновления API ключа...
python update_api_key.py
pause 