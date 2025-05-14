#!/usr/bin/env python
"""
Скрипт для прямой проверки API ключа Anthropic с подробной диагностикой.
Выводит детальную информацию о ключе и пытается выполнить тестовый запрос.
"""

import os
import sys
import re
import json
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def is_railway():
    """Проверяет, запущен ли скрипт в Railway"""
    return os.getenv('RAILWAY_ENVIRONMENT') is not None

def check_anthropic_key_directly():
    """Прямая проверка API ключа Anthropic через HTTP запрос"""
    print("\n========== ПРЯМАЯ ПРОВЕРКА API КЛЮЧА ANTHROPIC ==========")
    
    # Получаем API ключ
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not api_key:
        print("❌ API ключ не найден в переменных окружения!")
        return False
    
    # Выводим информацию о ключе
    print(f"📝 API ключ (длина: {len(api_key)})")
    print(f"📝 Префикс ключа: {api_key[:15]}...")
    print(f"📝 Суффикс ключа: ...{api_key[-4:]}")
    
    # Проверка формата ключа
    if api_key.startswith("sk-ant-api"):
        print("✓ Формат ключа: Новый формат (sk-ant-api...)")
        new_format = True
    elif api_key.startswith("sk-"):
        print("✓ Формат ключа: Старый формат (sk-...)")
        new_format = False
    else:
        print("❌ Неизвестный формат ключа! Ключ должен начинаться с 'sk-' или 'sk-ant-api'")
        return False
    
    # Выполняем тестовый запрос
    print("\n📡 Выполняю тестовый запрос к API Anthropic...")
    
    # Для нового формата ключа (Claude 3)
    if new_format:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 30,
            "messages": [
                {"role": "user", "content": "Напиши 'API ключ работает' на русском языке"}
            ]
        }
    # Для старого формата ключа (Claude 2)
    else:
        url = "https://api.anthropic.com/v1/complete"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-2.0",
            "max_tokens_to_sample": 30,
            "prompt": "\n\nHuman: Напиши 'API ключ работает' на русском языке\n\nAssistant: "
        }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        # Выводим информацию о запросе
        print(f"📤 URL: {url}")
        print(f"📤 Метод API: {'messages (новый)' if new_format else 'complete (старый)'}")
        print(f"📤 Статус ответа: {response.status_code}")
        
        # Если запрос успешен
        if response.status_code == 200:
            print("✅ API ключ работает корректно!")
            print("\n📥 Ответ API:")
            try:
                resp_data = response.json()
                print(json.dumps(resp_data, indent=2, ensure_ascii=False))
            except:
                print(response.text[:200])
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print("\n📥 Ответ API:")
            try:
                resp_data = response.json()
                print(json.dumps(resp_data, indent=2, ensure_ascii=False))
            except:
                print(response.text[:200])
            
            # Анализ специфических ошибок
            if response.status_code == 401:
                print("\n⚠️ Ошибка аутентификации (401):")
                print("- API ключ недействителен или отозван")
                print("- Возможно, ключ имеет неправильный формат")
                print("- Рекомендуется получить новый ключ в консоли Anthropic")
            
            return False
    except Exception as e:
        print(f"❌ Ошибка при выполнении запроса: {e}")
        return False

if __name__ == "__main__":
    print(f"🌐 Окружение: {'Railway' if is_railway() else 'Локальное'}")
    check_anthropic_key_directly() 