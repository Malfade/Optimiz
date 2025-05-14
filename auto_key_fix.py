#!/usr/bin/env python
"""
Скрипт для автоматического исправления API ключа Anthropic.
Проверяет и исправляет формат ключа без интерактивного ввода.
"""

import os
import sys
import re
import json
import requests
from dotenv import load_dotenv, set_key

# Загружаем переменные окружения
load_dotenv()

def is_railway():
    """Проверяет, запущен ли скрипт в Railway"""
    return os.getenv('RAILWAY_ENVIRONMENT') is not None

def fix_api_key_format():
    """Исправляет формат API ключа Anthropic для работы с новым API Claude 3"""
    print("\n========== АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ API КЛЮЧА ANTHROPIC ==========")
    
    # Проверяем, в каком окружении запущен скрипт
    is_cloud = is_railway()
    print(f"🌐 Окружение: {'Railway' if is_cloud else 'Локальное'}")
    
    # Получаем API ключ
    original_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not original_key:
        print("❌ API ключ не найден в переменных окружения!")
        return False
    
    # Выводим информацию о ключе
    print(f"📝 Текущий API ключ (длина: {len(original_key)})")
    print(f"📝 Начало ключа: {original_key[:15]}")
    
    # Обнаружение формата ключа
    if original_key.startswith("sk-ant-api"):
        print("✓ Ключ уже в новом формате Claude 3 (sk-ant-api...)")
        is_new_format = True
    elif original_key.startswith("sk-"):
        print("⚠️ Ключ в старом формате Claude 2 (sk-...)")
        is_new_format = False
    else:
        print("❌ Неизвестный формат ключа! Проверка других проблем...")
        is_new_format = False
    
    # Проверка на наличие кавычек
    new_key = original_key
    if new_key.startswith('"') and new_key.endswith('"'):
        print("⚠️ Обнаружены двойные кавычки в начале и конце ключа")
        new_key = new_key.strip('"')
    elif new_key.startswith("'") and new_key.endswith("'"):
        print("⚠️ Обнаружены одинарные кавычки в начале и конце ключа")
        new_key = new_key.strip("'")
    
    # Проверка на дополнительные пробелы
    if new_key != new_key.strip():
        print("⚠️ Обнаружены лишние пробелы в ключе")
        new_key = new_key.strip()
    
    # Если ключ изменился, сообщаем об этом
    if new_key != original_key:
        print(f"📝 Исправленный API ключ (длина: {len(new_key)})")
        print(f"📝 Начало ключа: {new_key[:15]}")
        
        # Обновляем переменную окружения в текущем процессе
        os.environ["ANTHROPIC_API_KEY"] = new_key
        
        # В локальном окружении можно также обновить .env файл
        if not is_cloud:
            env_path = ".env"
            if os.path.exists(env_path):
                set_key(env_path, "ANTHROPIC_API_KEY", new_key)
                print(f"✅ API ключ успешно обновлен в файле {env_path}")
            else:
                with open(env_path, "w") as f:
                    f.write(f"ANTHROPIC_API_KEY={new_key}\n")
                print(f"✅ Создан новый файл {env_path} с исправленным API ключом")
    else:
        print("✓ API ключ не требует форматирования")
    
    # Проверяем новый ключ на работоспособность
    print("\n📡 Проверяю API ключ на работоспособность...")
    
    # Для нового формата ключа (Claude 3)
    if new_key.startswith("sk-ant-api"):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": new_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 30,
            "messages": [
                {"role": "user", "content": "Say 'API key is working' in Russian"}
            ]
        }
    # Для старого формата ключа (Claude 2)
    else:
        url = "https://api.anthropic.com/v1/complete"
        headers = {
            "x-api-key": new_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-2.0",
            "max_tokens_to_sample": 30,
            "prompt": "\n\nHuman: Say 'API key is working' in Russian\n\nAssistant: "
        }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        # Выводим информацию о запросе
        print(f"📤 URL: {url}")
        print(f"📤 Метод API: {'messages (Claude 3)' if new_key.startswith('sk-ant-api') else 'complete (Claude 2)'}")
        print(f"📤 Статус ответа: {response.status_code}")
        
        # Если запрос успешен
        if response.status_code == 200:
            print("✅ API ключ работает корректно!")
            
            try:
                resp_data = response.json()
                content = ""
                if "content" in resp_data:
                    for item in resp_data["content"]:
                        if item.get("type") == "text":
                            content += item.get("text", "")
                elif "completion" in resp_data:
                    content = resp_data["completion"]
                
                if content:
                    print(f"📥 Ответ API: {content.strip()}")
            except:
                print("📥 Ответ получен, но не удалось извлечь текст")
            
            print("\n✅ API ключ исправлен и проверен успешно!")
            if is_cloud:
                print("⚠️ Примечание: в Railway исправление действует только для текущего запуска.")
                print("⚠️ Для постоянного решения исправьте ключ в панели управления Railway.")
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
                print("- Используйте скрипт get_new_key.py для получения нового ключа")
            
            if is_cloud:
                print("\n⚠️ В Railway для исправления API ключа:")
                print("1. Перейдите в панель управления Railway")
                print("2. Выберите ваш проект и сервис")
                print("3. Перейдите во вкладку Variables")
                print("4. Обновите переменную ANTHROPIC_API_KEY новым значением")
                print("5. Перезапустите сервис")
            
            return False
    except Exception as e:
        print(f"❌ Ошибка при выполнении запроса: {e}")
        if is_cloud:
            print("\n⚠️ В Railway для исправления API ключа:")
            print("1. Перейдите в панель управления Railway")
            print("2. Выберите ваш проект и сервис")
            print("3. Перейдите во вкладку Variables")
            print("4. Обновите переменную ANTHROPIC_API_KEY новым значением")
            print("5. Перезапустите сервис")
        return False

if __name__ == "__main__":
    fix_api_key_format() 