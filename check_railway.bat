@echo off
chcp 65001 >nul
title Проверка инфраструктуры Railway

echo Запуск проверки инфраструктуры бота на Railway...
python railway_fix.py
pause 