#!/usr/bin/env python
"""
Безопасная обертка для библиотеки Anthropic, которая перехватывает параметр proxies.
В ЭТОЙ ВЕРСИИ РЕАЛИЗОВАНЫ ЗАГЛУШКИ БЕЗ ЗАВИСИМОСТИ ОТ ANTHROPIC!

Адаптирован для работы с fallback_anthropic.
"""

import os
import sys
import logging
import inspect

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("safe_anthropic")

# Не импортируем больше оригинальную библиотеку
# import anthropic as original_anthropic

# Создаем заглушки для классов и функций
class SafeAnthropic:
    """
    Безопасная версия класса Anthropic, которая использует fallback_anthropic
    """
    def __init__(self, api_key=None, **kwargs):
        logger.info(f"Initializing SafeAnthropic with api_key and {len(kwargs)} additional kwargs")
        
        try:
            # Импортируем fallback_anthropic
            import fallback_anthropic
            
            # Создаем реальный клиент через fallback_anthropic
            logger.info("Creating Anthropic client using fallback_anthropic")
            self.client = fallback_anthropic.Anthropic(api_key=api_key)
            logger.info(f"Fallback Anthropic client created successfully")
            
        except Exception as e:
            logger.error(f"Error creating Anthropic client: {e}")
            raise RuntimeError(f"Failed to initialize fallback_anthropic: {e}")
    
    # Делегируем все вызовы к реальному клиенту
    def __getattr__(self, name):
        return getattr(self.client, name)

# Функция для создания клиентов 
def create_client(api_key=None, **kwargs):
    """
    Создает клиент Anthropic, используя fallback_anthropic.
    """
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not api_key:
        logger.error("API key not provided and not found in environment variables")
        raise ValueError("API key is required")
    
    try:
        logger.info(f"Creating client with SafeAnthropic (with clean environment)")
        client = SafeAnthropic(api_key=api_key, **kwargs)
        logger.info(f"Successfully created client with SafeAnthropic")
        return client
    except Exception as e:
        logger.error(f"Error creating client with SafeAnthropic: {e}")
        raise

# Экспортируем безопасный класс
Anthropic = SafeAnthropic

# Экспорт констант для обратной совместимости
HUMAN_PROMPT = "\n\nHuman: "
AI_PROMPT = "\n\nAssistant: "

# Версия библиотеки
__version__ = "0.19.1-safe-fallback"

# Сообщаем о успешной инициализации
logger.info("SafeAnthropic: Модуль успешно инициализирован")
print("[SAFE ANTHROPIC] Безопасная обертка для библиотеки Anthropic успешно инициализирована (использует fallback_anthropic)") 