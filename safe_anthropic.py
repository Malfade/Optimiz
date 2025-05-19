#!/usr/bin/env python
"""
Безопасная обертка для библиотеки Anthropic, которая перехватывает параметр proxies.
Этот модуль следует импортировать вместо оригинальной библиотеки anthropic.
"""

import os
import sys
import logging
import inspect

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("safe_anthropic")

# Импортируем оригинальную библиотеку
import anthropic as original_anthropic

# Создаем безопасную версию Anthropic
class SafeAnthropic(original_anthropic.Anthropic):
    """
    Безопасная версия класса Anthropic, которая удаляет параметр proxies
    перед вызовом оригинального конструктора.
    """
    def __init__(self, *args, **kwargs):
        logger.info(f"Initializing SafeAnthropic with kwargs: {kwargs}")
        
        # Удаляем параметр proxies, если он присутствует
        if 'proxies' in kwargs:
            logger.info(f"Removing proxies parameter: {kwargs['proxies']}")
            kwargs.pop('proxies')
        
        # Вызываем оригинальный конструктор
        try:
            super().__init__(*args, **kwargs)
            logger.info(f"SafeAnthropic initialized successfully")
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                # Если есть еще неизвестные аргументы, логируем их
                logger.error(f"TypeError in SafeAnthropic.__init__: {e}")
                logger.error(f"Original args: {args}")
                logger.error(f"Original kwargs: {kwargs}")
                logger.error(f"Original signature: {inspect.signature(original_anthropic.Anthropic.__init__)}")
                
                # Пытаемся определить и удалить проблемные аргументы
                valid_params = inspect.signature(original_anthropic.Anthropic.__init__).parameters
                valid_param_names = set(valid_params.keys())
                
                # Удаляем все параметры, которых нет в сигнатуре
                unknown_params = set(kwargs.keys()) - valid_param_names
                for param in unknown_params:
                    logger.info(f"Removing unknown parameter: {param}={kwargs[param]}")
                    kwargs.pop(param)
                
                # Пробуем снова с очищенными параметрами
                super().__init__(*args, **kwargs)
                logger.info(f"SafeAnthropic initialized successfully after removing unknown parameters")
            else:
                # Другие ошибки пробрасываем
                raise

# Функция для создания клиентов без proxies
def create_client(api_key=None):
    """
    Создает клиент Anthropic, безопасно удаляя параметр proxies.
    """
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    logger.info(f"Creating client with SafeAnthropic")
    return SafeAnthropic(api_key=api_key)

# Экспортируем безопасный класс
Anthropic = SafeAnthropic

# Экспортируем другие компоненты оригинального модуля
for name in dir(original_anthropic):
    if not name.startswith('_') and name != 'Anthropic':
        globals()[name] = getattr(original_anthropic, name)

# Версия библиотеки
try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution("anthropic").version
    logger.info(f"Anthropic library version: {__version__}")
except Exception as e:
    logger.warning(f"Could not determine anthropic version: {e}")
    __version__ = "unknown"

# Сообщаем о успешной инициализации
logger.info("SafeAnthropic: Модуль успешно инициализирован")
print("[SAFE ANTHROPIC] Безопасная обертка для библиотеки Anthropic успешно инициализирована") 