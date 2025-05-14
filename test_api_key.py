#!/usr/bin/env python
"""
Проверка API ключа Anthropic
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
import anthropic

# Импортируем наш вспомогательный модуль
from anthropic_helper import get_api_key_with_prefix, create_anthropic_client

# Загрузка переменных окружения
load_dotenv()

async def test_api_key():
    """Асинхронная функция для тестирования API ключа"""
    print("======== Тестирование API ключа Anthropic ========")
    
    # Получаем API ключ с правильным префиксом
    api_key = get_api_key_with_prefix()
    
    if not api_key:
        print("❌ API ключ не найден в переменных окружения")
        return False
    
    print(f"📝 API ключ найден (длина: {len(api_key)})")
    print(f"📝 Начало ключа: {api_key[:15]}...")
    
    # Создаем клиент
    client, method_name, error = await create_anthropic_client()
    
    if error:
        print(f"❌ Ошибка при создании клиента: {error}")
        return False
    
    print(f"✅ Клиент успешно создан, используя метод: {method_name}")
    
    # Тестируем API-запрос
    print("\n🔍 Выполнение тестового запроса к API...")
    
    try:
        if method_name == "completion":
            # Старый API
            response = client.completion(
                prompt="\n\nHuman: Привет, как дела?\n\nAssistant:",
                model="claude-2",
                max_tokens_to_sample=100,
                temperature=0.7
            )
            result = response.completion
        else:
            # Новый API
            messages = [
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": "Привет, как дела?"
                        }
                    ]
                }
            ]
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=100,
                messages=messages
            )
            result = response.content[0].text
        
        print(f"✅ Тестовый запрос выполнен успешно!")
        print(f"📝 Ответ от API: {result[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении тестового запроса: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_api_key()) 