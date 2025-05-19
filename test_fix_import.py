#!/usr/bin/env python
"""
Тестовый скрипт для проверки импорта через fix_imports
"""
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_imports")

logger.info("1. Запуск теста импортов...")

try:
    # Импортируем fix_imports
    import fix_imports
    logger.info("2. fix_imports импортирован успешно")
    
    # Импортируем anthropic
    import anthropic
    logger.info(f"3. anthropic импортирован успешно, модуль: {anthropic.__name__}")
    logger.info(f"4. Версия anthropic: {getattr(anthropic, '__version__', 'unknown')}")
    
    # Тестируем создание клиента
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        logger.info("5. API ключ найден, тестируем создание клиента...")
        client = anthropic.Anthropic(api_key=api_key)
        logger.info(f"6. Клиент успешно создан: {client.__class__.__name__}")
        
        # Тестируем отправку запроса
        logger.info("7. Тестируем отправку запроса...")
        try:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Test"}]
            )
            logger.info(f"8. Запрос успешно отправлен, ответ: {response.content[0].text if response.content else 'Нет ответа'}")
        except Exception as e:
            logger.error(f"8. Ошибка при отправке запроса: {e}")
    else:
        logger.warning("5. API ключ не найден, пропускаем тесты с клиентом")
    
    logger.info("9. Все тесты завершены успешно")
except Exception as e:
    logger.error(f"ОШИБКА: {e}")
    
print("Тест импортов завершен, проверьте логи") 