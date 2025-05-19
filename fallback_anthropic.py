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
from typing import List, Dict, Any, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fallback_anthropic")

# Константы для API
API_URL = "https://api.anthropic.com"
API_VERSION = "2023-06-01"  # Последняя стабильная версия

class Response:
    """Простой класс для представления ответа от API"""
    def __init__(self, content, **kwargs):
        self.content = content
        for key, value in kwargs.items():
            setattr(self, key, value)

class MessageContent:
    """Класс для представления содержимого сообщения"""
    def __init__(self, text):
        self.text = text

class Messages:
    """Класс для работы с сообщениями"""
    def __init__(self, client):
        self.client = client
    
    def create(self, model: str, messages: List[Dict[str, Any]], max_tokens: int = 1000, **kwargs):
        """Создает новый запрос к модели Claude"""
        try:
            logger.info(f"Creating message with model {model}, max_tokens={max_tokens}")
            
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
                data[key] = value
            
            # Выполнение запроса без использования прокси
            logger.info("Sending request directly to Anthropic API")
            response = requests.post(
                f"{API_URL}/v1/messages",
                headers=headers,
                json=data,
                timeout=60  # Увеличиваем таймаут
            )
            
            # Проверка ответа
            response.raise_for_status()
            result = response.json()
            
            # Преобразование результата в объект
            content = [MessageContent(c["text"]) for c in result.get("content", [])]
            return Response(content, **{k: v for k, v in result.items() if k != "content"})
        
        except Exception as e:
            logger.error(f"Error in messages.create: {e}")
            # Если сообщение об ошибке содержит JSON, извлекаем его
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                try:
                    error_json = json.loads(e.response.text)
                    logger.error(f"API error details: {error_json}")
                except:
                    logger.error(f"API response: {e.response.text}")
            raise

class Anthropic:
    """Минимальная реализация клиента Anthropic для Railway"""
    def __init__(self, api_key=None, **kwargs):
        logger.info(f"Initializing Fallback Anthropic client with {len(kwargs)} kwargs")
        
        # Игнорируем параметр proxies
        if 'proxies' in kwargs:
            logger.info("Ignoring proxies parameter")
        
        # Сохраняем API ключ
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError("API key is required. Provide it as a parameter or set ANTHROPIC_API_KEY environment variable.")
        
        # Инициализируем компоненты
        self.messages = Messages(self)
        logger.info("Fallback Anthropic client initialized successfully")

# Версия "библиотеки"
__version__ = "0.19.0-fallback"

# Класс Client для обратной совместимости
Client = Anthropic

# Дополнительные константы
HUMAN_PROMPT = "\n\nHuman: "
AI_PROMPT = "\n\nAssistant: "

# Сообщение о инициализации
logger.info(f"Fallback Anthropic module initialized (version {__version__})")
print(f"[FALLBACK ANTHROPIC] Simplified Anthropic client initialized (version {__version__})") 