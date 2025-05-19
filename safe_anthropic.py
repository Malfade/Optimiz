#!/usr/bin/env python
"""
Безопасная обертка для библиотеки Anthropic, которая перехватывает параметр proxies.
Этот модуль следует импортировать вместо оригинальной библиотеки anthropic.
"""

import os
import sys
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("safe_anthropic")

# Импортируем оригинальную библиотеку
import anthropic as original_anthropic

# Создаем копию оригинального модуля
sys.modules['original_anthropic'] = original_anthropic

# Создаем безопасную версию класса Anthropic
class SafeAnthropic(original_anthropic.Anthropic):
    """
    Безопасная версия класса Anthropic, которая игнорирует неподдерживаемые параметры.
    """
    def __init__(self, *args, **kwargs):
        # Удаляем параметр proxies, если он присутствует
        if 'proxies' in kwargs:
            logger.info(f"SafeAnthropic: Удаляем параметр proxies из kwargs")
            del kwargs['proxies']
        
        # Вызываем оригинальный конструктор
        try:
            super().__init__(*args, **kwargs)
        except TypeError as e:
            # Если всё ещё возникает ошибка с аргументами, логируем её и пробрасываем
            logger.error(f"Ошибка при инициализации Anthropic: {e}")
            logger.error(f"Аргументы: args={args}, kwargs={kwargs}")
            raise

# Заменяем оригинальный класс на наш безопасный
original_anthropic.Anthropic = SafeAnthropic

# Обертка для создания клиента без параметра proxies
def create_client(api_key=None):
    """
    Создает безопасный клиент Anthropic, перехватывая параметр proxies.
    """
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    try:
        return SafeAnthropic(api_key=api_key)
    except Exception as e:
        logger.error(f"Ошибка при создании клиента: {e}")
        raise

# Экспортируем имя класса
Anthropic = SafeAnthropic

# Также экспортируем другие полезные классы
Client = original_anthropic.Client if hasattr(original_anthropic, 'Client') else None
messages = original_anthropic.messages if hasattr(original_anthropic, 'messages') else None

# Сообщаем о успешной инициализации
logger.info("SafeAnthropic: Модуль успешно инициализирован")
print("[SAFE ANTHROPIC] Безопасная обертка для библиотеки Anthropic успешно инициализирована") 