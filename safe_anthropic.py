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
            # Очищаем переменные окружения HTTP_PROXY и HTTPS_PROXY
            # которые Railway может автоматически добавлять
            original_http_proxy = os.environ.pop('HTTP_PROXY', None)
            original_https_proxy = os.environ.pop('HTTPS_PROXY', None)
            original_http_proxy_lower = os.environ.pop('http_proxy', None)
            original_https_proxy_lower = os.environ.pop('https_proxy', None)
            
            # Создаем клиент БЕЗ параметра proxies
            logger.info("Creating Anthropic client without proxies parameter")
            self.client = original_anthropic.Anthropic(api_key=api_key)
            
            # Восстанавливаем переменные окружения
            if original_http_proxy:
                os.environ['HTTP_PROXY'] = original_http_proxy
            if original_https_proxy:
                os.environ['HTTPS_PROXY'] = original_https_proxy
            if original_http_proxy_lower:
                os.environ['http_proxy'] = original_http_proxy_lower
            if original_https_proxy_lower:
                os.environ['https_proxy'] = original_https_proxy_lower
                
            logger.info(f"Original Anthropic client created successfully")
        except Exception as e:
            logger.error(f"Error creating Anthropic client: {e}")
            # Попробуем еще один способ - создание без конструктора
            try:
                # Используем другой подход к созданию клиента - через модуль напрямую
                logger.info("Trying alternative way to create client")
                
                # Смотрим какие библиотеки есть для создания клиента
                if hasattr(original_anthropic, 'Client'):
                    logger.info("Using Client class")
                    self.client = original_anthropic.Client(api_key=api_key)
                else:
                    # Если все попытки не удались, выбрасываем исключение
                    raise e
            except Exception as alt_error:
                logger.error(f"Alternative client creation also failed: {alt_error}")
                raise e
    
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
    
    # Очищаем переменные окружения HTTP_PROXY и HTTPS_PROXY перед созданием клиента
    original_http_proxy = os.environ.pop('HTTP_PROXY', None)
    original_https_proxy = os.environ.pop('HTTPS_PROXY', None)
    original_http_proxy_lower = os.environ.pop('http_proxy', None)
    original_https_proxy_lower = os.environ.pop('https_proxy', None)
    
    try:
        logger.info(f"Creating client with SafeAnthropic (with clean environment)")
        client = SafeAnthropic(api_key=api_key)
        logger.info(f"Successfully created client with SafeAnthropic")
        return client
    except Exception as e:
        logger.error(f"Error creating client with SafeAnthropic: {e}")
        # Попробуем создать напрямую через оригинальный модуль
        try:
            logger.info("Trying to create client directly")
            client = original_anthropic.Anthropic(api_key=api_key)
            logger.info("Successfully created client directly")
            return client
        except Exception as direct_error:
            logger.error(f"Direct client creation failed too: {direct_error}")
            raise e
    finally:
        # Восстанавливаем переменные окружения
        if original_http_proxy:
            os.environ['HTTP_PROXY'] = original_http_proxy
        if original_https_proxy:
            os.environ['HTTPS_PROXY'] = original_https_proxy
        if original_http_proxy_lower:
            os.environ['http_proxy'] = original_http_proxy_lower
        if original_https_proxy_lower:
            os.environ['https_proxy'] = original_https_proxy_lower

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