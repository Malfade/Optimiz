"""
Вспомогательный модуль для работы с API Anthropic.
Обеспечивает совместимость с разными версиями библиотеки и форматами API ключей.
"""

import os
import re
import logging
import pkg_resources
import asyncio
from typing import Tuple, Union, Dict, Any, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_anthropic_version() -> str:
    """
    Получает установленную версию библиотеки anthropic.
    """
    try:
        version = pkg_resources.get_distribution("anthropic").version
        logger.info(f"Обнаружена версия библиотеки anthropic: {version}")
        return version
    except pkg_resources.DistributionNotFound:
        logger.warning("Библиотека anthropic не установлена!")
        return "0.0.0"

def is_valid_anthropic_key(api_key: str) -> bool:
    """
    Проверяет, имеет ли API ключ правильный формат.
    Поддерживаются ключи старого формата (sk-...) и нового формата (sk-ant-api...).
    """
    if not api_key:
        return False
    
    # Проверка для новых ключей Claude 3 (sk-ant-api...)
    new_key_pattern = r'^sk-ant-api\w{2}-[A-Za-z0-9-_]{70,100}$'
    # Проверка для старых ключей Claude 2 (sk-...)
    old_key_pattern = r'^sk-[A-Za-z0-9]{40,60}$'
    
    is_new_format = bool(re.match(new_key_pattern, api_key))
    is_old_format = bool(re.match(old_key_pattern, api_key))
    
    if not (is_new_format or is_old_format):
        logger.warning(f"API ключ не соответствует ожидаемому формату: {api_key[:10]}...")
    
    return is_new_format or is_old_format

def get_api_key_with_prefix() -> str:
    """
    Получает API ключ из переменных окружения и проверяет его формат.
    Для новых версий библиотеки (>=0.51.0) добавляет префикс, если его нет.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not api_key:
        logger.error("API ключ не найден в переменных окружения!")
        return ""
    
    # Проверка ключа
    api_key = api_key.strip()
    version = get_anthropic_version()
    
    # Для новых версий библиотеки используем новый формат ключа
    if api_key and is_valid_anthropic_key(api_key):
        logger.info(f"API ключ подготовлен (длина: {len(api_key)})")
    else:
        logger.warning(f"API ключ имеет некорректный формат или отсутствует")
    
    return api_key

async def create_anthropic_client() -> Tuple[Optional[Any], Optional[str], Optional[str]]:
    """
    Создает клиент API Anthropic в зависимости от версии библиотеки.
    Возвращает кортеж (клиент, метод, ошибка).
    """
    api_key = get_api_key_with_prefix()
    if not api_key:
        return None, None, "API ключ не найден или имеет неверный формат"
    
    version = get_anthropic_version()
    
    try:
        # Для версии 0.19.0 и выше используем новый клиент
        import anthropic
        
        # Проверяем особенности версии
        if float(version.split('.')[0]) > 0 or float(version.split('.')[1]) >= 19:
            logger.info(f"Используется клиент Anthropic версии >= 0.19.0 (новейший API)")
            client = anthropic.Anthropic(api_key=api_key)
            return client, "messages.create", None
        else:
            # Для старых версий библиотеки
            logger.info(f"Используется клиент Anthropic версии < 0.19.0 (старый API)")
            client = anthropic.Anthropic(api_key=api_key)
            return client, "completions.create", None
            
    except Exception as e:
        error_msg = f"Ошибка при создании клиента Anthropic: {str(e)}"
        logger.error(error_msg)
        return None, None, error_msg 