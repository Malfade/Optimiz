@echo off
chcp 65001 >nul
title Обновление API ключа Anthropic

echo =================================================
echo Утилита обновления API ключа Anthropic
echo =================================================

python get_new_key.py

pause 