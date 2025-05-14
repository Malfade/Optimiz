"""
Вспомогательный модуль для работы с Anthropic API.
Помогает использовать API с разными версиями библиотеки.
"""

import os
import logging
import re
import asyncio
import pkg_resources

# Настройка логирования
logger = logging.getLogger("anthropic_helper")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def get_api_key_with_prefix():
    """
    Получает API ключ из переменных окружения и добавляет нужный префикс в зависимости от версии API.
    Версии библиотеки 0.5.10+ и 0.6.0+ требуют ключи формата sk-ant-api03-XXX...
    Версии до 0.5.10 требуют ключи формата sk-XXX...
    
    Returns:
        str: отформатированный API ключ или None, если ключ не найден
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        logger.warning("API ключ не найден в переменных окружения")
        return None
    
    # Удаляем кавычки, если они есть (Railway часто добавляет их)
    if (api_key.startswith('"') and api_key.endswith('"')) or (api_key.startswith("'") and api_key.endswith("'")):
        original_key = api_key
        api_key = api_key.strip("'\"")
        logger.info(f"Удалены кавычки из API ключа (было: {len(original_key)}, стало: {len(api_key)})")
    
    # Определяем версию библиотеки
    try:
        anthropic_version = pkg_resources.get_distribution("anthropic").version
        logger.info(f"Обнаружена версия библиотеки anthropic: {anthropic_version}")
        
        # Проверяем необходимость добавления префикса
        is_new_version = False
        if anthropic_version.startswith("0.5") and int(anthropic_version.split(".")[1]) >= 10:
            is_new_version = True
        elif anthropic_version.startswith("0.") and int(anthropic_version.split(".")[1]) >= 6:
            is_new_version = True
            
        # Для новых версий API (>=0.51.0) проверяем и добавляем префикс
        if is_new_version:
            # Добавляем префикс, если нужно
            if not api_key.startswith("sk-ant-api03-"):
                if api_key.startswith("sk-ant-api"):
                    # Ключ уже имеет похожий префикс, но возможно неполный
                    logger.warning(f"API ключ имеет нестандартный префикс '{api_key[:12]}...'")
                    # Оставляем как есть
                elif api_key.startswith("sk-"):
                    # Ключ имеет старый префикс, заменяем его
                    api_key = api_key.replace("sk-", "sk-ant-api03-")
                    logger.info("API ключ преобразован в формат для нового API (добавлен префикс sk-ant-api03-)")
                else:
                    # Ключ без префикса, добавляем полный префикс
                    api_key = f"sk-ant-api03-{api_key}"
                    logger.info("API ключ преобразован в формат для нового API (добавлен префикс sk-ant-api03-)")
        else:
            # Для старых версий API (<0.51.0) проверяем и добавляем префикс sk-
            if api_key.startswith("sk-ant-api"):
                # Удаляем лишний префикс
                api_key = api_key.replace("sk-ant-api03-", "sk-")
                logger.info("API ключ преобразован в формат для старого API (заменен префикс на sk-)")
            elif not api_key.startswith("sk-"):
                # Добавляем префикс sk-
                api_key = f"sk-{api_key}"
                logger.info("API ключ преобразован в формат для старого API (добавлен префикс sk-)")
    
    except Exception as e:
        logger.error(f"Ошибка при определении версии библиотеки: {e}")
        # В случае ошибки, добавляем префикс sk-ant-api03- как более универсальный
        if not api_key.startswith("sk-"):
            api_key = f"sk-ant-api03-{api_key}"
            logger.info("API ключ преобразован в формат для нового API (добавлен префикс sk-ant-api03-)")
    
    logger.info(f"API ключ подготовлен (длина: {len(api_key)})")
    
    # Валидация ключа по формату
    if not is_valid_anthropic_key(api_key):
        logger.warning(f"API ключ не соответствует ожидаемому формату: {api_key[:12]}...")
    
    return api_key

def is_valid_anthropic_key(api_key):
    """
    Проверяет, соответствует ли API ключ ожидаемому формату.
    
    Args:
        api_key (str): API ключ для проверки
        
    Returns:
        bool: True, если формат соответствует ожидаемому
    """
    if not api_key:
        return False
    
    # Для новых ключей (API v0.5.10+)
    if api_key.startswith("sk-ant-api"):
        pattern = r'^sk-ant-api03-[A-Za-z0-9]{24,}$'
        return bool(re.match(pattern, api_key))
    
    # Для старых ключей (API до v0.5.10)
    elif api_key.startswith("sk-"):
        pattern = r'^sk-[A-Za-z0-9]{24,}$'
        return bool(re.match(pattern, api_key))
    
    return False

async def create_anthropic_client():
    """
    Создает клиент Anthropic API в зависимости от версии библиотеки.
    
    Returns:
        tuple: (client, метод, ошибка)
            - client: экземпляр клиента Anthropic
            - метод: имя метода для вызова (completion или messages.create)
            - ошибка: сообщение об ошибке или None
    """
    api_key = get_api_key_with_prefix()
    
    if not api_key:
        return None, None, "API ключ не найден"
    
    try:
        # Импортируем библиотеку
        import anthropic
        
        # Определяем версию библиотеки
        anthropic_version = pkg_resources.get_distribution("anthropic").version
        
        # Проверяем является ли версия >= 0.51.0 или >= 0.6.0
        is_new_version = False
        if anthropic_version.startswith("0.5") and int(anthropic_version.split(".")[1]) >= 10:
            is_new_version = True
        elif anthropic_version.startswith("0.") and int(anthropic_version.split(".")[1]) >= 6:
            is_new_version = True
        
        if is_new_version:
            # Код для API v0.51.0+
            logger.info("Используется клиент Anthropic версии >= 0.51.0 (новый API)")
            
            # Для версий API 0.51.0+ и 0.6.0+
            # Используем новый метод инициализации и messages.create
            if not api_key.startswith("sk-ant-api"):
                logger.warning(f"Ключ может быть неправильного формата для API версии {anthropic_version}")
            
            try:
                client = anthropic.Anthropic(api_key=api_key)
                return client, "messages.create", None
            except Exception as e:
                logger.error(f"Ошибка при инициализации клиента новой версии: {e}")
                # Попробуем создать клиент с явным указанием всех параметров
                try:
                    client = anthropic.Anthropic(
                        api_key=api_key,
                        base_url="https://api.anthropic.com",
                        timeout=300
                    )
                    return client, "messages.create", None
                except Exception as e2:
                    return None, None, f"Ошибка создания клиента: {e2}"
        else:
            # Код для API до v0.51.0
            logger.info("Используется клиент Anthropic версии < 0.51.0 (старый API)")
            
            # Для старых версий API
            # Используем старый метод инициализации и completion
            if not api_key.startswith("sk-"):
                logger.warning(f"Ключ может быть неправильного формата для API версии {anthropic_version}")
            
            try:
                client = anthropic.Client(api_key=api_key)
                return client, "completion", None
            except Exception as e:
                logger.error(f"Ошибка при инициализации клиента старой версии: {e}")
                return None, None, f"Ошибка создания клиента: {e}"
                
    except Exception as e:
        logger.error(f"Ошибка при импорте или инициализации библиотеки: {e}")
        return None, None, f"Ошибка инициализации: {e}" 