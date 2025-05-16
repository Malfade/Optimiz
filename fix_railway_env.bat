@echo off
chcp 65001 >nul
title Исправление API ключа в Railway

echo Запуск утилиты исправления API ключа в Railway...
python fix_railway_env.py
pause 