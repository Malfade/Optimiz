#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для проверки развертывания в Railway.
Проверяет корректность импортов и доступность API.
"""

import logging
import os
import sys
import time
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("railway_check")

# Информация о среде
logger.info("=== Проверка развертывания в Railway ===")
logger.info(f"Python версия: {sys.version}")
logger.info(f"Текущая директория: {os.getcwd()}")
logger.info(f"Системные переменные окружения: {list(filter(lambda x: not x.startswith('_'), os.environ.keys()))}")

# Проверка наличия необходимых переменных окружения
required_vars = ["API_KEY", "TELEGRAM_BOT_TOKEN"]
missing_vars = [var for var in required_vars if not os.environ.get(var)]

if missing_vars:
    logger.warning(f"Отсутствуют переменные окружения: {', '.join(missing_vars)}")
else:
    logger.info("Все необходимые переменные окружения найдены.")

# Проверка импортов
logger.info("Проверка импортов...")
try:
    import fix_imports
    logger.info("✓ fix_imports успешно импортирован.")
except ImportError as e:
    logger.error(f"✗ Ошибка импорта fix_imports: {e}")

try:
    import fallback_anthropic
    logger.info(f"✓ fallback_anthropic успешно импортирован (версия: {fallback_anthropic.__version__}).")
except ImportError as e:
    logger.error(f"✗ Ошибка импорта fallback_anthropic: {e}")

try:
    import safe_anthropic
    logger.info("✓ safe_anthropic успешно импортирован.")
except ImportError as e:
    logger.error(f"✗ Ошибка импорта safe_anthropic: {e}")

try:
    import optimization_bot
    logger.info("✓ optimization_bot успешно импортирован.")
except ImportError as e:
    logger.error(f"✗ Ошибка импорта optimization_bot: {e}")

# Проверка создания клиента Anthropic
logger.info("Проверка создания клиента Anthropic...")
api_key = os.environ.get("API_KEY", "")
if api_key:
    try:
        client = safe_anthropic.create_client()
        if client.initialized:
            logger.info("✓ Клиент Anthropic успешно создан.")
        else:
            logger.warning("✗ Клиент Anthropic не инициализирован.")
    except Exception as e:
        logger.error(f"✗ Ошибка при создании клиента Anthropic: {e}")
else:
    logger.warning("Невозможно создать клиент Anthropic без API_KEY.")

# Проверка файлов
logger.info("Проверка наличия необходимых файлов...")
required_files = [
    "main.py", "fix_imports.py", "fallback_anthropic.py", 
    "safe_anthropic.py", "optimization_bot.py", "requirements.txt"
]
for file in required_files:
    if os.path.exists(file):
        logger.info(f"✓ Файл {file} найден (размер: {os.path.getsize(file)} байт).")
    else:
        logger.error(f"✗ Файл {file} не найден!")

# Проверка соединения
logger.info("Проверка соединения...")
try:
    import requests
    response = requests.get("https://www.anthropic.com", timeout=10)
    logger.info(f"✓ Соединение с anthropic.com установлено (код ответа: {response.status_code}).")
except Exception as e:
    logger.error(f"✗ Ошибка соединения с anthropic.com: {e}")

# Сохранение отчета
logger.info("Создание отчета о проверке...")
report = {
    "timestamp": datetime.now().isoformat(),
    "python_version": sys.version,
    "environment_variables": list(filter(lambda x: not x.startswith('_'), os.environ.keys())),
    "missing_env_vars": missing_vars,
    "required_files_status": {file: os.path.exists(file) for file in required_files}
}

with open("railway_check_report.json", "w") as f:
    json.dump(report, f, indent=2)

logger.info("Отчет сохранен в railway_check_report.json")
logger.info("=== Проверка завершена ===")

# Финальное сообщение для Railway логов
print("\n" + "="*50)
print("RAILWAY DEPLOYMENT CHECK COMPLETED")
print(f"Timestamp: {datetime.now().isoformat()}")
print("="*50 + "\n")

if missing_vars or not all(os.path.exists(file) for file in required_files):
    print("⚠️ Обнаружены проблемы, требующие внимания!")
else:
    print("✅ Все проверки пройдены успешно!") 