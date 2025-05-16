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
        super().__init__(*args, **kwargs)

# Заменяем оригинальный класс на наш безопасный
original_anthropic.Anthropic = SafeAnthropic

# Обертка для создания клиента без параметра proxies
def create_client(api_key=None):
    """
    Создает безопасный клиент Anthropic, перехватывая параметр proxies.
    """
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    return SafeAnthropic(api_key=api_key)

# Экспортируем имя класса
Anthropic = SafeAnthropic

# Сообщаем о успешной инициализации
logger.info("SafeAnthropic: Модуль успешно инициализирован")
print("[SAFE ANTHROPIC] Безопасная обертка для библиотеки Anthropic успешно инициализирована") 