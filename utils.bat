@echo off
chcp 65001 >nul
title Утилиты для OptimizationBot

:menu
cls
echo ========================================
echo    Утилиты для OptimizationBot
echo ========================================
echo.
echo  1. Проверить API ключ
echo  2. Обновить API ключ
echo  3. Исправить формат API ключа
echo  4. Запустить бота
echo  5. Проверить инфраструктуру Railway
echo  6. Исправить API ключ в Railway
echo  7. Выход
echo.
echo ========================================
echo.

set /p choice=Выберите действие (1-7): 

if "%choice%"=="1" goto test_key
if "%choice%"=="2" goto update_key
if "%choice%"=="3" goto fix_key
if "%choice%"=="4" goto start_bot
if "%choice%"=="5" goto check_railway
if "%choice%"=="6" goto fix_railway_key
if "%choice%"=="7" goto exit
goto menu

:test_key
cls
echo Запуск проверки API ключа...
python test_api_key.py
pause
goto menu

:update_key
cls
echo Запуск утилиты обновления API ключа...
python update_api_key.py
pause
goto menu

:fix_key
cls
echo Запуск исправления формата API ключа...
python fix_env_key.py
pause
goto menu

:start_bot
cls
echo Запуск бота...
python optimization_bot.py
pause
goto menu

:check_railway
cls
echo Проверка инфраструктуры Railway...
python railway_fix.py
pause
goto menu

:fix_railway_key
cls
echo Исправление API ключа в Railway...
python fix_railway_env.py
pause
goto menu

:exit
exit 