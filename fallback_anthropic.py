#!/usr/bin/env python
"""
Минимальная реализация клиента Anthropic для использования в Railway.
Этот файл можно использовать вместо библиотеки anthropic, когда ничего другое не работает.
Файл работает путем прямых HTTP-запросов к API Anthropic, минуя официальную библиотеку.

Пример использования:
```python
import fallback_anthropic as anthropic
client = anthropic.Anthropic(api_key="your_api_key")
response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, world!"}]
)
print(response.content[0].text)
```
"""

import os
import json
import logging
import requests
import traceback
from typing import List, Dict, Any, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fallback_anthropic")

# Константы для API
API_URL = "https://api.anthropic.com"
API_VERSION = "2023-06-01"  # Последняя стабильная версия
DEFAULT_MODELS = ["claude-3-opus-20240229", "claude-3-haiku-20240307", "claude-3-sonnet-20240229"]

class Response:
    """Простой класс для представления ответа от API"""
    def __init__(self, content, **kwargs):
        self.content = content
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        if hasattr(self, 'content') and self.content:
            preview = self.content[0].text[:50] + "..." if len(self.content[0].text) > 50 else self.content[0].text
            return f"Response(content=[{preview}])"
        return "Response(content=[])"

class MessageContent:
    """Класс для представления содержимого сообщения"""
    def __init__(self, text):
        self.text = text
    
    def __str__(self):
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"MessageContent(text='{preview}')"

class Messages:
    """Класс для работы с сообщениями"""
    def __init__(self, client):
        self.client = client
    
    def create(self, model: str, messages: List[Dict[str, Any]], max_tokens: int = 1000, **kwargs):
        """Создает новый запрос к модели Claude"""
        try:
            logger.info(f"Создаем сообщение с моделью {model}, max_tokens={max_tokens}")
            
            # Проверка модели
            if not model or not isinstance(model, str):
                logger.warning(f"Некорректная модель: {model}, используем claude-3-haiku-20240307")
                model = "claude-3-haiku-20240307"
            
            # Подготовка запроса
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.client.api_key,
                "anthropic-version": API_VERSION
            }
            
            # Формирование данных запроса
            data = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages
            }
            
            # Добавляем дополнительные параметры
            for key, value in kwargs.items():
                if key != 'proxies':  # Игнорируем proxies
                    data[key] = value
            
            # Логируем параметры запроса (без API ключа)
            safe_headers = {k: v for k, v in headers.items() if k != 'x-api-key'}
            logger.info(f"Заголовки запроса: {safe_headers}")
            logger.info(f"Параметры запроса: model={model}, max_tokens={max_tokens}, messages_count={len(messages)}")
            
            # Очищаем переменные окружения прокси перед запросом
            saved_proxies = {}
            for env_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                if env_var in os.environ:
                    saved_proxies[env_var] = os.environ[env_var]
                    del os.environ[env_var]
            
            try:
                # Выполнение запроса без использования прокси
                logger.info("Отправляем запрос напрямую в Anthropic API...")
                response = requests.post(
                    f"{API_URL}/v1/messages",
                    headers=headers,
                    json=data,
                    timeout=120  # Увеличиваем таймаут до 2 минут
                )
                
                # Проверка ответа
                response.raise_for_status()
                result = response.json()
                
                # Преобразование результата в объект
                content = [MessageContent(c["text"]) for c in result.get("content", [])]
                resp_obj = Response(content, **{k: v for k, v in result.items() if k != "content"})
                
                # Логируем успешный результат
                logger.info(f"Успешно получен ответ от API: {str(resp_obj)}")
                return resp_obj
            
            finally:
                # Восстанавливаем переменные окружения
                for env_var, value in saved_proxies.items():
                    os.environ[env_var] = value
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сетевого запроса: {e}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_details = e.response.json()
                    logger.error(f"Детали ошибки API: {error_details}")
                except:
                    logger.error(f"Текст ответа API: {e.response.text}")
            
            # Возвращаем объект Response с сообщением об ошибке
            error_content = MessageContent(f"Ошибка API: {str(e)}")
            return Response([error_content], error=str(e), status_code=getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500)
            
        except Exception as e:
            logger.error(f"Неожиданная ошибка в messages.create: {e}")
            logger.error(traceback.format_exc())
            
            # Возвращаем объект Response с сообщением об ошибке
            error_content = MessageContent(f"Внутренняя ошибка: {str(e)}")
            return Response([error_content], error=str(e), status_code=500)

class Anthropic:
    """Минимальная реализация клиента Anthropic для Railway"""
    def __init__(self, api_key=None, **kwargs):
        logger.info(f"Инициализация Fallback Anthropic клиента с {len(kwargs)} kwargs")
        
        # Игнорируем параметр proxies и все остальные
        if kwargs:
            ignored_params = ', '.join(kwargs.keys())
            logger.info(f"Игнорируем параметры: {ignored_params}")
        
        # Сохраняем API ключ
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            logger.error("API ключ не предоставлен!")
            raise ValueError("API ключ обязателен. Предоставьте его как параметр или установите переменную окружения ANTHROPIC_API_KEY.")
        
        # Маскируем API ключ в логах
        masked_key = self.api_key[:4] + "*" * (len(self.api_key) - 8) + self.api_key[-4:] if len(self.api_key) > 8 else "****"
        logger.info(f"API ключ получен (маскирован): {masked_key}")
        
        # Инициализируем компоненты
        self.messages = Messages(self)
        logger.info("Fallback Anthropic клиент успешно инициализирован")

# Версия "библиотеки"
__version__ = "0.19.1-fallback"

# Класс Client для обратной совместимости
Client = Anthropic

# Дополнительные константы для обратной совместимости
HUMAN_PROMPT = "\n\nHuman: "
AI_PROMPT = "\n\nAssistant: "

# Поддерживаемые модели
CLAUDE_MODELS = {
    "claude-3-opus-20240229": {
        "name": "Claude 3 Opus",
        "context_window": 200000,
        "tokens_per_minute": 50000,
    },
    "claude-3-sonnet-20240229": {
        "name": "Claude 3 Sonnet",
        "context_window": 200000,
        "tokens_per_minute": 80000,
    },
    "claude-3-haiku-20240307": {
        "name": "Claude 3 Haiku",
        "context_window": 200000,
        "tokens_per_minute": 100000,
    },
}

# Вспомогательные функции
def get_max_tokens(model_name=None):
    """Возвращает максимальное количество токенов для модели"""
    if model_name and model_name in CLAUDE_MODELS:
        return CLAUDE_MODELS[model_name].get("context_window", 100000)
    return 100000

# Создаем глобальный клиент для использования по умолчанию
DEFAULT_CLIENT = None

# Функция create_client для обратной совместимости
def create_client(api_key=None, **kwargs):
    """Создает клиент Anthropic с заданным API ключом"""
    logger.info("Вызов create_client")
    global DEFAULT_CLIENT
    
    client = Anthropic(api_key=api_key, **kwargs)
    DEFAULT_CLIENT = client
    return client

# Сообщение о инициализации
logger.info(f"Fallback Anthropic модуль инициализирован (версия {__version__})")
print(f"[FALLBACK ANTHROPIC] Упрощенный клиент Anthropic инициализирован (версия {__version__})") 