@echo off
chcp 65001 >nul
title Deploy to Railway

echo ===================================================
echo Подготовка к деплою Telegram бота на Railway
echo ===================================================
echo.

:: Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python не найден. Установите Python версии 3.9 или выше.
    goto end
)

:: Проверка наличия Railway CLI
railway version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Railway CLI не найден. Хотите установить? (y/n)
    set /p install_railway=
    if /i "%install_railway%"=="y" (
        echo Установка Railway CLI...
        npm i -g @railway/cli
        if %errorlevel% neq 0 (
            echo [ERROR] Не удалось установить Railway CLI. Проверьте, установлен ли Node.js.
            goto end
        )
    ) else (
        echo [INFO] Продолжаем без Railway CLI. Вы сможете выполнить деплой через веб-интерфейс.
    )
)

:: Запуск проверки Railway Ready
echo.
echo Запуск проверки настроек для Railway...
echo.
python check_railway_ready.py
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Обнаружены проблемы в настройке. Хотите продолжить? (y/n)
    set /p continue=
    if /i not "%continue%"=="y" goto end
)

:: Вывод сводки
echo.
echo ===================================================
echo                  СВОДКА ПРОЕКТА
echo ===================================================
echo.
echo Файлы:
dir /b optimization_bot.py safe_anthropic.py railway.json Procfile requirements.txt

echo.
echo Содержимое railway.json:
type railway.json

echo.
echo Содержимое Procfile:
type Procfile

echo.
echo ===================================================
echo                ОПЦИИ ДЕПЛОЯ
echo ===================================================
echo.
echo 1. Деплой через Railway CLI (требуется авторизация)
echo 2. Инструкции по деплою через веб-интерфейс
echo 3. Выход
echo.
set /p choice=Выберите опцию (1-3): 

if "%choice%"=="1" (
    echo.
    echo Авторизация в Railway...
    railway login
    
    echo.
    echo Начинаем деплой...
    railway up
    
    echo.
    echo Проверьте статус деплоя на dashboard.railway.app
) else if "%choice%"=="2" (
    echo.
    echo ===================================================
    echo       ИНСТРУКЦИИ ПО ДЕПЛОЮ ЧЕРЕЗ ВЕБ-ИНТЕРФЕЙС
    echo ===================================================
    echo.
    echo 1. Откройте сайт railway.app и войдите в аккаунт
    echo 2. Нажмите "New Project"
    echo 3. Выберите "Deploy from GitHub repo" и подключите ваш репозиторий
    echo 4. После создания проекта, перейдите в раздел "Variables"
    echo 5. Добавьте следующие переменные окружения:
    echo    - TELEGRAM_TOKEN: ваш токен телеграм бота
    echo    - ANTHROPIC_API_KEY: ваш API ключ от Claude
    echo    - RAILWAY_ENVIRONMENT: production
    echo.
    echo Для открытия веб-интерфейса Railway?
    set /p open_browser=Открыть веб-сайт Railway? (y/n):
    
    if /i "%open_browser%"=="y" (
        start https://railway.app/dashboard
    )
) else (
    echo Выход из программы.
)

:end
echo.
echo Нажмите любую клавишу для выхода...
pause >nul 