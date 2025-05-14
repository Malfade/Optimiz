"""
Вспомогательные функции для работы с Anthropic API
Обеспечивает совместимость с разными версиями API
"""

import os
import logging
import re
import pkg_resources
import asyncio

# Настройка логгера
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_api_key_with_prefix():
    """
    Получает API ключ из переменных окружения и добавляет префикс, если необходимо
    
    Returns:
        str: API ключ с правильным префиксом
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        logger.error("API ключ Anthropic не найден в переменных окружения")
        return None
    
    # Определяем версию библиотеки
    try:
        anthropic_version = pkg_resources.get_distribution("anthropic").version
        logger.info(f"Обнаружена версия библиотеки anthropic: {anthropic_version}")
        
        # Для новых версий проверяем формат ключа
        is_new_version = False
        if anthropic_version.startswith("0.5") and int(anthropic_version.split(".")[1]) >= 10:
            is_new_version = True
        elif anthropic_version.startswith("0.") and int(anthropic_version.split(".")[1]) >= 6:
            is_new_version = True
        
        # Проверяем и корректируем формат ключа если нужно
        if is_new_version:
            # Для версий >=0.51.0 нужен формат с префиксом sk-ant-api03-
            if not api_key.startswith("sk-ant-api"):
                if api_key.startswith("sk-"):
                    api_key = api_key.replace("sk-", "sk-ant-api03-")
                else:
                    api_key = f"sk-ant-api03-{api_key}"
                logger.info("API ключ преобразован в формат для нового API (добавлен префикс sk-ant-api03-)")
        else:
            # Для старых версий
            if not api_key.startswith("sk-"):
                api_key = f"sk-{api_key}"
                logger.info("API ключ преобразован в формат для старого API (добавлен префикс sk-)")
    
    except Exception as e:
        logger.error(f"Ошибка при определении версии библиотеки: {e}")
        # По умолчанию добавляем общий префикс
        if not api_key.startswith("sk-"):
            api_key = f"sk-{api_key}"
    
    # Возвращаем проверенный ключ
    logger.info(f"API ключ подготовлен (длина: {len(api_key)})")
    return api_key

def is_valid_anthropic_key(api_key):
    """
    Проверяет, соответствует ли API ключ формату Anthropic
    
    Args:
        api_key: Ключ API для проверки
        
    Returns:
        bool: True если ключ соответствует формату, иначе False
    """
    if not api_key:
        return False
    
    # Паттерны для разных форматов ключей
    old_pattern = r'^sk-[A-Za-z0-9]{40,}$'
    new_pattern = r'^sk-ant-api[0-9]+-[A-Za-z0-9-]{40,}$'
    
    return bool(re.match(old_pattern, api_key) or re.match(new_pattern, api_key))

async def create_anthropic_client():
    """
    Создает клиент Anthropic API с правильным форматом ключа
    
    Returns:
        tuple: (client, client_method, error)
    """
    import anthropic
    
    api_key = get_api_key_with_prefix()
    
    if not api_key:
        return None, None, "API ключ не найден"
    
    if not is_valid_anthropic_key(api_key):
        logger.warning(f"API ключ не соответствует ожидаемому формату: {api_key[:10]}...")
    
    # Определяем версию библиотеки
    try:
        anthropic_version = pkg_resources.get_distribution("anthropic").version
        
        # Для версии >= 0.51.0 (новый API)
        if anthropic_version.startswith("0.5") and int(anthropic_version.split(".")[1]) >= 10 or anthropic_version.startswith("0.6") or anthropic_version.startswith("0.7"):
            logger.info("Используется клиент Anthropic версии >= 0.51.0 (новый API)")
            try:
                client = anthropic.Anthropic(api_key=api_key)
                return client, "messages.create", None
            except Exception as e:
                return None, None, f"Ошибка при создании клиента Anthropic нового API: {e}"
        else:
            # Для версии 0.3.x-0.5.9 (старый API)
            logger.info("Используется клиент Anthropic версии <= 0.5.9 (старый API)")
            try:
                client = anthropic.Client(api_key=api_key)
                return client, "completion", None
            except Exception as e:
                return None, None, f"Ошибка при создании клиента Anthropic старого API: {e}"
    
    except Exception as e:
        return None, None, f"Ошибка при определении версии библиотеки: {e}" 