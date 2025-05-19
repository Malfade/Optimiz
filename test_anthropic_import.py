#!/usr/bin/env python
"""
Тест для проверки корректности работы модуля safe_anthropic
"""

import os
import logging
import dotenv
from pprint import pprint

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_anthropic")

# Загружаем переменные окружения
dotenv.load_dotenv()

# Выводим версию библиотеки
import pkg_resources
anthropic_version = pkg_resources.get_distribution("anthropic").version
print(f"Версия библиотеки anthropic: {anthropic_version}")

# Проверяем обычный импорт и импорт через safe_anthropic
print("\n--- Тест 1: Импорт оригинальной библиотеки ---")
try:
    import anthropic
    print("✅ Импорт anthropic успешен")
    
    # Пробуем создать клиент с proxies
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    print(f"API ключ: {api_key[:10]}...{api_key[-4:]}")
    
    client = anthropic.Anthropic(
        api_key=api_key,
        proxies={"http": None, "https": None}  # Это вызовет ошибку на 0.19.0
    )
    print("✅ Создан клиент с proxies")
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\n--- Тест 2: Импорт через safe_anthropic ---")
try:
    # Сбрасываем кэш модулей
    import sys
    if 'anthropic' in sys.modules:
        del sys.modules['anthropic']
    
    import safe_anthropic as anthropic
    print("✅ Импорт safe_anthropic успешен")
    
    # Пробуем создать клиент с proxies
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    client = anthropic.Anthropic(
        api_key=api_key,
        proxies={"http": None, "https": None}  # Это должно работать
    )
    print("✅ Создан клиент с proxies через safe_anthropic")
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\n--- Тест 3: Создание через helper функцию ---")
try:
    from safe_anthropic import create_client
    client = create_client()
    print("✅ Создан клиент через helper функцию")
    
    # Проверяем тип клиента
    print(f"Тип клиента: {type(client).__name__}")
except Exception as e:
    print(f"❌ Ошибка: {e}") 