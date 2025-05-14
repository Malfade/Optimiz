#!/usr/bin/env python
"""
Обновление API ключа Anthropic
"""

import os
import sys
import re
from dotenv import load_dotenv, set_key

def update_api_key():
    """Обновляет API ключ в файле .env"""
    print("======== Обновление API ключа Anthropic ========")
    
    # Загружаем текущие переменные окружения
    load_dotenv()
    
    # Получаем текущий ключ
    current_key = os.getenv("ANTHROPIC_API_KEY")
    if current_key:
        print(f"📝 Текущий ключ найден (длина: {len(current_key)})")
        print(f"📝 Начало ключа: {current_key[:10]}...")
    else:
        print("❌ Текущий API ключ не найден в файле .env")
    
    # Запрашиваем новый ключ
    new_key = input("\nВведите новый API ключ Anthropic (без префикса sk-): ")
    
    if not new_key:
        print("❌ Новый ключ не был введен. Отмена операции.")
        return
    
    # Форматируем ключ для API v0.51.0+
    if not new_key.startswith("sk-"):
        formatted_key = f"sk-ant-api03-{new_key}"
    else:
        if not new_key.startswith("sk-ant-api03-"):
            formatted_key = new_key.replace("sk-", "sk-ant-api03-")
        else:
            formatted_key = new_key
    
    # Проверяем формат ключа с помощью регулярного выражения
    pattern = r'^sk-ant-api03-[A-Za-z0-9-]{40,}$'
    if not re.match(pattern, formatted_key):
        print("⚠️ Внимание: Формат ключа может быть неправильным.")
        confirm = input("Продолжить обновление? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Операция отменена пользователем.")
            return
    
    # Обновляем ключ в файле .env
    try:
        env_path = ".env"
        set_key(env_path, "ANTHROPIC_API_KEY", formatted_key)
        print(f"✅ API ключ успешно обновлен в файле {env_path}")
        print(f"📝 Новый ключ: {formatted_key[:10]}...{formatted_key[-5:]}")
    except Exception as e:
        print(f"❌ Ошибка при обновлении ключа: {e}")
        print("⚠️ Попробуйте обновить файл .env вручную.")

if __name__ == "__main__":
    update_api_key() 