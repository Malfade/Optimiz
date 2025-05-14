#!/usr/bin/env python
"""
Автоматическое исправление формата API ключа в файле .env
"""

import os
import re
from dotenv import load_dotenv, set_key
import pkg_resources

def fix_api_key():
    """
    Исправляет формат API ключа в файле .env в соответствии с версией библиотеки
    
    Returns:
        bool: True если успешно исправлен, False в случае ошибки
    """
    print("======== Автоматическое исправление API ключа ========")
    
    # Загружаем текущие переменные окружения
    load_dotenv()
    
    # Получаем текущий ключ
    current_key = os.getenv("ANTHROPIC_API_KEY")
    if not current_key:
        print("❌ API ключ не найден в файле .env")
        return False
    
    print(f"📝 Текущий ключ найден (длина: {len(current_key)})")
    
    # Определяем версию библиотеки
    try:
        anthropic_version = pkg_resources.get_distribution("anthropic").version
        print(f"📝 Найдена библиотека anthropic версии {anthropic_version}")
        
        # Проверяем необходимость обновления формата
        is_new_version = False
        if anthropic_version.startswith("0.5") and int(anthropic_version.split(".")[1]) >= 10:
            is_new_version = True
        elif anthropic_version.startswith("0.") and int(anthropic_version.split(".")[1]) >= 6:
            is_new_version = True
        
        if is_new_version:
            # Для версий >=0.51.0 нужен формат с префиксом sk-ant-api03-
            print("📝 Для текущей версии API требуется префикс sk-ant-api03-")
            
            if current_key.startswith("sk-ant-api"):
                print("✅ Ключ уже имеет правильный формат")
                return True
            
            # Форматируем ключ
            if current_key.startswith("sk-"):
                new_key = current_key.replace("sk-", "sk-ant-api03-")
            else:
                new_key = f"sk-ant-api03-{current_key}"
            
            print(f"📝 Преобразование ключа: {current_key[:5]}... -> {new_key[:15]}...")
                
        else:
            # Для старых версий
            print("📝 Для текущей версии API требуется префикс sk-")
            
            if current_key.startswith("sk-"):
                print("✅ Ключ уже имеет правильный формат")
                return True
            
            new_key = f"sk-{current_key}"
            print(f"📝 Преобразование ключа: {current_key[:5]}... -> {new_key[:5]}...")
        
        # Обновляем ключ в файле .env
        env_path = ".env"
        set_key(env_path, "ANTHROPIC_API_KEY", new_key)
        print(f"✅ API ключ успешно обновлен в файле {env_path}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    if fix_api_key():
        print("✅ Операция завершена успешно")
    else:
        print("❌ Операция завершена с ошибками")
    input("Нажмите Enter для выхода...") 