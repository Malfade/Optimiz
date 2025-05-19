#!/usr/bin/env python
"""
Безопасная обертка для библиотеки Anthropic, которая перехватывает параметр proxies.
Этот модуль следует импортировать вместо оригинальной библиотеки anthropic.

Адаптирован для работы с версией 0.19.0, где параметр proxies присутствует в сигнатуре,
но вызывает ошибку при использовании.
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
        proxies_value = None
        if 'proxies' in kwargs:
            logger.info(f"Removing proxies parameter: {kwargs['proxies']}")
            proxies_value = kwargs.pop('proxies')
        
        # Получаем сигнатуру родительского метода
        orig_sig = inspect.signature(original_anthropic.Anthropic.__init__)
        valid_params = set(orig_sig.parameters.keys())
        
        # Удаляем все параметры, которых нет в сигнатуре или которые вызывают ошибки
        known_problematic_params = {'proxies'}  # параметры, которые есть в сигнатуре, но вызывают ошибки
        filtered_kwargs = {}
        
        for key, value in kwargs.items():
            # Не добавляем известные проблемные параметры и неизвестные параметры
            if key in known_problematic_params:
                logger.info(f"Skipping known problematic parameter: {key}={value}")
                continue
            if key not in valid_params and key != 'self':
                logger.info(f"Skipping unknown parameter: {key}={value}")
                continue
            filtered_kwargs[key] = value
        
        logger.info(f"Calling original __init__ with filtered kwargs: {filtered_kwargs}")
        
        # Вызываем оригинальный конструктор с очищенными параметрами
        try:
            super().__init__(*args, **filtered_kwargs)
            logger.info(f"SafeAnthropic initialized successfully")
        except TypeError as e:
            # Если все еще возникают ошибки, логируем и пытаемся решить
            logger.error(f"TypeError in SafeAnthropic.__init__: {e}")
            logger.error(f"Original args: {args}")
            logger.error(f"Filtered kwargs: {filtered_kwargs}")
            logger.error(f"Original signature: {orig_sig}")
            
            # Создаем минимальный набор параметров
            minimal_kwargs = {}
            if 'api_key' in filtered_kwargs:
                minimal_kwargs['api_key'] = filtered_kwargs['api_key']
            
            logger.info(f"Trying with minimal kwargs: {minimal_kwargs}")
            super().__init__(*args, **minimal_kwargs)
            logger.info(f"SafeAnthropic initialized successfully with minimal parameters")

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

# Прямой патч класса Client, если он существует
if hasattr(original_anthropic, 'Client'):
    original_client_init = original_anthropic.Client.__init__
    
    def patched_client_init(self, *args, **kwargs):
        if 'proxies' in kwargs:
            logger.info(f"Removing proxies from Client initialization: {kwargs['proxies']}")
            kwargs.pop('proxies')
        return original_client_init(self, *args, **kwargs)
    
    original_anthropic.Client.__init__ = patched_client_init
    logger.info("Patched original_anthropic.Client.__init__ to remove proxies parameter")

# Версия библиотеки
try:
    __version__ = original_anthropic.__version__
    logger.info(f"Anthropic library version: {__version__}")
except Exception as e:
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