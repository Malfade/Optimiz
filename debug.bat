@echo off
chcp 65001 >nul
title Debug

echo Запуск режима отладки...
python debug_package.py
pause 