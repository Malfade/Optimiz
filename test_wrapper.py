#!/usr/bin/env python
"""
Тест для проверки нашей обертки Anthropic
"""

import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_wrapper")

# Загружаем переменные окружения
load_dotenv()

# Импортируем нашу обертку
print("Импортируем wrapper...")
import anthropic_wrapper

# Выводим версию библиотеки
print(f"Версия библиотеки anthropic: {anthropic_wrapper.anthropic_version}")

# Создаем и тестируем клиент
print("\nСоздаем клиент через wrapper...")
try:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ API ключ не найден в переменных окружения")
    else:
        print(f"API ключ (первые 10 символов): {api_key[:10]}...")
    
    # Создаем клиент через helper функцию
    client = anthropic_wrapper.create_client(api_key=api_key)
    print(f"✅ Клиент успешно создан: {type(client).__name__}")
    
    # Пробуем создать клиент напрямую с параметром proxies
    client2 = anthropic_wrapper.anthropic.Anthropic(
        api_key=api_key,
        proxies={"http": None, "https": None}  # Это должно быть удалено оберткой
    )
    print(f"✅ Клиент успешно создан с proxies: {type(client2).__name__}")
    
except Exception as e:
    print(f"❌ Ошибка при создании клиента: {e}")

print("\nТест завершен!") 