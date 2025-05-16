#!/usr/bin/env python
"""
Скрипт для получения нового API ключа Anthropic с правильным форматом.
Помогает получить и проверить ключ для использования в боте.
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

def get_new_api_key():
    """Инструкции по получению нового API ключа и его проверка"""
    print("\n========== ПОЛУЧЕНИЕ НОВОГО API КЛЮЧА ANTHROPIC ==========")
    
    # Проверяем, в каком окружении запущен скрипт
    is_cloud = is_railway()
    print(f"🌐 Окружение: {'Railway' if is_cloud else 'Локальное'}")
    
    if is_cloud:
        print("\n⚠️ Вы запустили этот скрипт в Railway.")
        print("⚠️ В облачном окружении невозможно интерактивно получить ключ.")
        print("⚠️ Пожалуйста, следуйте инструкциям ниже, чтобы обновить ключ в Railway:")
        print("\n1. Зайдите на сайт https://console.anthropic.com/")
        print("2. Войдите в свой аккаунт или создайте новый")
        print("3. Перейдите в раздел API Keys")
        print("4. Создайте новый ключ (если нужно)")
        print("5. Скопируйте ключ (он должен начинаться с 'sk-ant-api' для Claude 3)")
        print("6. Перейдите в панель управления Railway")
        print("7. Выберите ваш проект и сервис")
        print("8. Перейдите во вкладку Variables")
        print("9. Обновите переменную ANTHROPIC_API_KEY новым значением")
        print("10. Перезапустите сервис\n")
        return
    
    # В локальном окружении - интерактивное получение ключа
    print("\n📌 Инструкции по получению нового API ключа:")
    print("1. Зайдите на сайт https://console.anthropic.com/")
    print("2. Войдите в свой аккаунт или создайте новый")
    print("3. Перейдите в раздел API Keys")
    print("4. Создайте новый ключ (если нужно)")
    print("5. Скопируйте ключ и вставьте его ниже\n")
    
    # Получаем текущий ключ
    current_key = os.getenv("ANTHROPIC_API_KEY", "")
    if current_key:
        print(f"📝 Текущий API ключ (длина: {len(current_key)})")
        print(f"📝 Начало ключа: {current_key[:15]}")
    else:
        print("📝 Текущий API ключ отсутствует")
    
    # Запрашиваем новый ключ
    new_key = input("\n🔑 Введите новый API ключ: ").strip()
    
    if not new_key:
        print("❌ Вы не ввели ключ. Операция отменена.")
        return
    
    # Проверяем формат ключа
    if new_key.startswith("sk-ant-api"):
        print("✓ Формат ключа: Новый формат (sk-ant-api...)")
        new_format = True
    elif new_key.startswith("sk-"):
        print("✓ Формат ключа: Старый формат (sk-...)")
        new_format = False
    else:
        print("❌ Неизвестный формат ключа! Ключ должен начинаться с 'sk-' или 'sk-ant-api'")
        retry = input("Хотите продолжить несмотря на ошибку формата? (y/n): ").strip().lower()
        if retry != 'y':
            return
    
    # Проверяем ключ
    print("\n📡 Проверяю новый API ключ...")
    
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
    # Для старого формата ключа
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
        print(f"📤 Статус ответа: {response.status_code}")
        
        # Если запрос успешен
        if response.status_code == 200:
            print("✅ API ключ работает корректно!")
            
            # Сохраняем ключ в .env файл
            env_path = ".env"
            if os.path.exists(env_path):
                set_key(env_path, "ANTHROPIC_API_KEY", new_key)
                print(f"✅ API ключ успешно сохранен в файл {env_path}")
            else:
                with open(env_path, "w") as f:
                    f.write(f"ANTHROPIC_API_KEY={new_key}\n")
                print(f"✅ Создан новый файл {env_path} с API ключом")
                
            # Обновляем переменную окружения в текущем процессе
            os.environ["ANTHROPIC_API_KEY"] = new_key
            
            print("✅ API ключ успешно обновлен и проверен!")
            print("\n🤖 Теперь бот должен работать корректно.")
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
            
            retry = input("\nХотите сохранить этот ключ несмотря на ошибку? (y/n): ").strip().lower()
            if retry == 'y':
                # Сохраняем ключ в .env файл
                env_path = ".env"
                if os.path.exists(env_path):
                    set_key(env_path, "ANTHROPIC_API_KEY", new_key)
                    print(f"✅ API ключ сохранен в файл {env_path} (несмотря на ошибку)")
                else:
                    with open(env_path, "w") as f:
                        f.write(f"ANTHROPIC_API_KEY={new_key}\n")
                    print(f"✅ Создан новый файл {env_path} с API ключом (несмотря на ошибку)")
                
                # Обновляем переменную окружения в текущем процессе
                os.environ["ANTHROPIC_API_KEY"] = new_key
                return True
            
            return False
    except Exception as e:
        print(f"❌ Ошибка при выполнении запроса: {e}")
        
        retry = input("\nХотите сохранить этот ключ несмотря на ошибку? (y/n): ").strip().lower()
        if retry == 'y':
            # Сохраняем ключ в .env файл
            env_path = ".env"
            if os.path.exists(env_path):
                set_key(env_path, "ANTHROPIC_API_KEY", new_key)
                print(f"✅ API ключ сохранен в файл {env_path} (несмотря на ошибку)")
            else:
                with open(env_path, "w") as f:
                    f.write(f"ANTHROPIC_API_KEY={new_key}\n")
                print(f"✅ Создан новый файл {env_path} с API ключом (несмотря на ошибку)")
            
            # Обновляем переменную окружения в текущем процессе
            os.environ["ANTHROPIC_API_KEY"] = new_key
            return True
        
        return False

if __name__ == "__main__":
    get_new_api_key() 