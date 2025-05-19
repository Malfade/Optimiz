#!/usr/bin/env python
"""
Обертка для Anthropic API, которая гарантирует, что параметр 'proxies' не будет передан.
Этот скрипт нужно импортировать и использовать вместо прямого импорта библиотеки anthropic.
"""

import os
import logging
import importlib
import sys

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anthropic_wrapper")

# Попытка импорта безопасной версии, если уже существует
try:
    import safe_anthropic
    logger.info("Импортирован безопасный модуль safe_anthropic")
    anthropic = safe_anthropic
except ImportError:
    # Если safe_anthropic не найден, используем оригинальный модуль с патчем
    try:
        import anthropic as original_anthropic
        # Сохраняем копию оригинального класса
        _original_anthropic_class = original_anthropic.Anthropic
        
        # Создаем безопасную обертку
        class SafeAnthropicWrapper(_original_anthropic_class):
            """Безопасная обертка для Anthropic, удаляющая проблемные параметры"""
            def __init__(self, *args, **kwargs):
                logger.info("SafeAnthropicWrapper: Инициализация с безопасными параметрами")
                # Удаляем proxies из параметров
                if 'proxies' in kwargs:
                    logger.info(f"SafeAnthropicWrapper: Удален параметр proxies={kwargs['proxies']}")
                    del kwargs['proxies']
                
                # Вызываем оригинальный конструктор
                super().__init__(*args, **kwargs)
        
        # Заменяем оригинальный класс на наш безопасный
        original_anthropic.Anthropic = SafeAnthropicWrapper
        anthropic = original_anthropic
        logger.info("Создана безопасная обертка для Anthropic")
    except ImportError:
        logger.error("Не удалось импортировать ни safe_anthropic, ни оригинальный модуль anthropic")
        raise

# Функция для создания клиента безопасным способом
def create_client(api_key=None):
    """
    Создает клиент Anthropic без параметра proxies
    
    Args:
        api_key: API ключ (если None, используется из окружения ANTHROPIC_API_KEY)
    
    Returns:
        Экземпляр клиента Anthropic
    """
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    logger.info("Создание клиента Anthropic через безопасную обертку")
    return anthropic.Anthropic(api_key=api_key)

# Версия библиотеки
try:
    import pkg_resources
    anthropic_version = pkg_resources.get_distribution("anthropic").version
    logger.info(f"Версия библиотеки anthropic: {anthropic_version}")
except Exception as e:
    logger.warning(f"Не удалось определить версию библиотеки anthropic: {e}")

# Проверяем, загружен ли модуль успешно
if anthropic:
    logger.info("Антропик обертка успешно инициализирована")
    print("[ANTHROPIC WRAPPER] Безопасная обертка для библиотеки Anthropic успешно инициализирована!")
else:
    logger.error("Не удалось инициализировать антропик обертку")
    print("[ANTHROPIC WRAPPER ERROR] Не удалось создать безопасную обертку для Anthropic!") 