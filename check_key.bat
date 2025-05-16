@echo off
chcp 65001 >nul
title Проверка API ключа Anthropic

echo =================================================
echo Утилита проверки API ключа Anthropic
echo =================================================

python check_anthropic_key.py

pause 