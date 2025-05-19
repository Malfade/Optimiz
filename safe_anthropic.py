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
class SafeAnthropic:
    """
    Безопасная версия класса Anthropic, которая удаляет параметр proxies
    перед вызовом оригинального конструктора.
    """
    def __init__(self, api_key=None, **kwargs):
        logger.info(f"Initializing SafeAnthropic with api_key and {len(kwargs)} additional kwargs")
        
        # Удаляем параметр proxies, если он присутствует
        if 'proxies' in kwargs:
            logger.info(f"Removing proxies parameter")
            del kwargs['proxies']
        
        # Создаем реальный Anthropic клиент
        try:
            self.client = original_anthropic.Anthropic(api_key=api_key)
            logger.info(f"Original Anthropic client created successfully")
        except Exception as e:
            logger.error(f"Error creating Anthropic client: {e}")
            raise
    
    # Делегируем все вызовы к реальному клиенту
    def __getattr__(self, name):
        return getattr(self.client, name)

# Функция для создания клиентов без proxies
def create_client(api_key=None):
    """
    Создает клиент Anthropic, безопасно удаляя параметр proxies.
    """
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not api_key:
        logger.error("API key not provided and not found in environment variables")
        raise ValueError("API key is required")
    
    logger.info(f"Creating client with SafeAnthropic")
    return SafeAnthropic(api_key=api_key)

# Применяем прямой патч к оригинальному классу
original_init = original_anthropic.Anthropic.__init__

def patched_init(self, *args, **kwargs):
    # Удаляем проблемный параметр proxies
    if 'proxies' in kwargs:
        logger.info(f"Removing proxies from Anthropic.__init__")
        del kwargs['proxies']
    
    # Вызываем оригинальный инициализатор
    return original_init(self, *args, **kwargs)

# Патчим оригинальный класс
original_anthropic.Anthropic.__init__ = patched_init
logger.info("Patched original_anthropic.Anthropic.__init__ to remove proxies parameter")

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
            logger.info(f"Removing proxies from Client initialization")
            del kwargs['proxies']
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