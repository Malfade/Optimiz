@echo off
chcp 65001 >nul
title Исправление API ключа

echo Запуск утилиты автоматического исправления API ключа...
python fix_env_key.py 