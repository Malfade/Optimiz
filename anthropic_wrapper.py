#!/usr/bin/env python
"""
Модуль-обертка для anthropic, который удаляет из kwargs параметр 'proxies'
и предотвращает создание проксирования в Railway.
"""
import os
import sys
import logging
import inspect
import importlib.util
from functools import wraps

# Настройка логирования
logger = logging.getLogger(__name__)

# Оригинальный модуль anthropic
try:
    # Сначала попробуем импортировать оригинальный anthropic
    spec = importlib.util.find_spec('anthropic')
    if spec is None:
        raise ImportError("Модуль anthropic не найден")
    
    # Сохраняем текущее значение sys.modules['anthropic']
    old_anthropic = sys.modules.get('anthropic')
    
    # Временно удаляем модуль из sys.modules, чтобы импортировать оригинальный
    if 'anthropic' in sys.modules:
        del sys.modules['anthropic']
    
    # Импортируем оригинальный модуль
    original_anthropic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original_anthropic)
    
    # Восстанавливаем старый модуль, если он был
    if old_anthropic:
        sys.modules['anthropic'] = old_anthropic
    
    logger.info("Оригинальный модуль anthropic успешно импортирован")
except Exception as e:
    logger.error(f"Ошибка при импорте оригинального модуля anthropic: {e}")
    raise

# Получаем версию оригинального модуля
__version__ = getattr(original_anthropic, '__version__', 'unknown')
logger.info(f"Версия оригинального модуля anthropic: {__version__}")

def remove_proxies_from_kwargs(func):
    """Декоратор, который удаляет 'proxies' из kwargs перед вызовом оригинального метода."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Проверяем, есть ли 'proxies' в kwargs
        if 'proxies' in kwargs:
            logger.info(f"Удаляем 'proxies' из kwargs при вызове {func.__name__}")
            del kwargs['proxies']
        
        # Сохраняем и очищаем переменные окружения прокси
        saved_env = {}
        for env_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            if env_var in os.environ:
                saved_env[env_var] = os.environ[env_var]
                del os.environ[env_var]
                logger.info(f"Временно удалили переменную окружения {env_var}")
        
        try:
            # Вызываем оригинальный метод
            result = func(*args, **kwargs)
            return result
        finally:
            # Восстанавливаем переменные окружения
            for env_var, value in saved_env.items():
                os.environ[env_var] = value
                logger.info(f"Восстановили переменную окружения {env_var}")
    
    return wrapper

# Создаем копию классов и функций из оригинального модуля
# с применением нашего декоратора ко всем методам __init__

# Патчим класс Anthropic
class Anthropic(original_anthropic.Anthropic):
    @remove_proxies_from_kwargs
    def __init__(self, *args, **kwargs):
        logger.info(f"Инициализация Anthropic с {len(args)} args и {len(kwargs)} kwargs")
        # Вызываем оригинальный метод
        try:
            super().__init__(*args, **kwargs)
            logger.info("Успешно инициализирован Anthropic")
        except Exception as e:
            logger.error(f"Ошибка при инициализации Anthropic: {e}")
            raise

# Патчим класс Client, если он существует
if hasattr(original_anthropic, 'Client'):
    class Client(original_anthropic.Client):
        @remove_proxies_from_kwargs
        def __init__(self, *args, **kwargs):
            logger.info(f"Инициализация Client с {len(args)} args и {len(kwargs)} kwargs")
            # Вызываем оригинальный метод
            try:
                super().__init__(*args, **kwargs)
                logger.info("Успешно инициализирован Client")
            except Exception as e:
                logger.error(f"Ошибка при инициализации Client: {e}")
                raise

# Функция для создания клиента (аналогично safe_anthropic)
def create_client(api_key=None, **kwargs):
    """
    Создает клиент Anthropic с безопасной обработкой параметра proxies.
    
    Args:
        api_key: API ключ для Anthropic. Если не указан, берется из ANTHROPIC_API_KEY.
        **kwargs: Дополнительные параметры для конструктора Anthropic.
    
    Returns:
        Экземпляр Anthropic с безопасной обработкой proxies.
    """
    logger.info("Вызов create_client")
    
    # Получаем API ключ
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("API ключ не указан и не найден в переменных окружения")
    
    # Удаляем proxies из kwargs, если есть
    if 'proxies' in kwargs:
        logger.info("Удаляем proxies из kwargs в create_client")
        del kwargs['proxies']
    
    # Проверяем доступность метода AsyncAnthropic
    client_class = Anthropic
    
    try:
        logger.info(f"Создаем клиент с классом {client_class.__name__}")
        return client_class(api_key=api_key, **kwargs)
    except Exception as e:
        logger.error(f"Ошибка при создании клиента: {e}")
        raise

# Добавляем все функции и константы из оригинального модуля
for name, obj in original_anthropic.__dict__.items():
    if name not in globals() and not name.startswith('_'):
        globals()[name] = obj

# Логируем успешную инициализацию модуля
logger.info("Модуль-обертка anthropic_wrapper успешно инициализирован")

# Test
if __name__ == "__main__":
    # Тестируем создание клиента
    try:
        client = create_client()
        logger.info("Тестовый клиент успешно создан!")
        
        # Проверим, что метод completion доступен
        if hasattr(client, 'completions'):
            logger.info("Метод completions доступен!")
        elif hasattr(client, 'messages'):
            logger.info("Метод messages доступен!")
        else:
            logger.warning("Ни completions, ни messages не найдены!")
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {e}") 