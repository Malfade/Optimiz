#!/bin/bash

# Установка цветов для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================================="
echo -e "      Подготовка к деплою Telegram бота на Railway"
echo -e "===================================================${NC}"
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python не найден. Установите Python версии 3.9 или выше.${NC}"
    exit 1
fi

# Проверка наличия Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}[INFO] Railway CLI не найден. Хотите установить? (y/n)${NC}"
    read -r install_railway
    if [[ "$install_railway" =~ ^[Yy]$ ]]; then
        echo "Установка Railway CLI..."
        npm i -g @railway/cli
        if [ $? -ne 0 ]; then
            echo -e "${RED}[ERROR] Не удалось установить Railway CLI. Проверьте, установлен ли Node.js.${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}[INFO] Продолжаем без Railway CLI. Вы сможете выполнить деплой через веб-интерфейс.${NC}"
    fi
fi

# Запуск проверки Railway Ready
echo ""
echo "Запуск проверки настроек для Railway..."
echo ""
python3 check_railway_ready.py
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}[WARNING] Обнаружены проблемы в настройке. Хотите продолжить? (y/n)${NC}"
    read -r continue
    if [[ ! "$continue" =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Вывод сводки
echo ""
echo -e "${GREEN}==================================================="
echo -e "                  СВОДКА ПРОЕКТА"
echo -e "===================================================${NC}"
echo ""
echo "Файлы:"
ls -la optimization_bot.py safe_anthropic.py railway.json Procfile requirements.txt

echo ""
echo "Содержимое railway.json:"
cat railway.json

echo ""
echo "Содержимое Procfile:"
cat Procfile

echo ""
echo -e "${GREEN}==================================================="
echo -e "                ОПЦИИ ДЕПЛОЯ"
echo -e "===================================================${NC}"
echo ""
echo "1. Деплой через Railway CLI (требуется авторизация)"
echo "2. Инструкции по деплою через веб-интерфейс"
echo "3. Выход"
echo ""
read -rp "Выберите опцию (1-3): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "Авторизация в Railway..."
    railway login
    
    echo ""
    echo "Начинаем деплой..."
    railway up
    
    echo ""
    echo "Проверьте статус деплоя на dashboard.railway.app"
elif [ "$choice" = "2" ]; then
    echo ""
    echo -e "${GREEN}==================================================="
    echo -e "       ИНСТРУКЦИИ ПО ДЕПЛОЮ ЧЕРЕЗ ВЕБ-ИНТЕРФЕЙС"
    echo -e "===================================================${NC}"
    echo ""
    echo "1. Откройте сайт railway.app и войдите в аккаунт"
    echo "2. Нажмите \"New Project\""
    echo "3. Выберите \"Deploy from GitHub repo\" и подключите ваш репозиторий"
    echo "4. После создания проекта, перейдите в раздел \"Variables\""
    echo "5. Добавьте следующие переменные окружения:"
    echo "   - TELEGRAM_TOKEN: ваш токен телеграм бота"
    echo "   - ANTHROPIC_API_KEY: ваш API ключ от Claude"
    echo "   - RAILWAY_ENVIRONMENT: production"
    echo ""
    read -rp "Открыть веб-сайт Railway в браузере? (y/n): " open_browser
    
    if [[ "$open_browser" =~ ^[Yy]$ ]]; then
        if command -v xdg-open &> /dev/null; then
            xdg-open https://railway.app/dashboard
        elif command -v open &> /dev/null; then
            open https://railway.app/dashboard
        else
            echo -e "${YELLOW}Не удалось открыть браузер автоматически. Посетите https://railway.app/dashboard${NC}"
        fi
    fi
else
    echo "Выход из программы."
fi

echo ""
echo -e "${GREEN}Завершено!${NC}" 