#!/usr/bin/env python
import os
import sys
import pkg_resources
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Получение версии Python
python_version = sys.version
print(f"Версия Python: {python_version}")

# Получение установленной версии Anthropic
try:
    anthropic_version = pkg_resources.get_distribution("anthropic").version
    print(f"Установленная версия anthropic: {anthropic_version}")
except pkg_resources.DistributionNotFound:
    print("Библиотека anthropic не установлена")

# Проверка переменных окружения
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
if anthropic_key:
    print(f"API ключ Anthropic: {anthropic_key[:5]}...{anthropic_key[-5:]}")
    print(f"Длина ключа: {len(anthropic_key)}")
    print(f"Начинается с sk-: {anthropic_key.startswith('sk-')}")
else:
    print("API ключ Anthropic не найден")

# Проверка импорта библиотеки Anthropic
try:
    import anthropic
    print("Библиотека anthropic успешно импортирована")
    
    # Пробуем создать клиент
    try:
        client = anthropic.Client(api_key=anthropic_key)
        print("Клиент anthropic.Client успешно создан")
    except Exception as e:
        print(f"Ошибка при создании anthropic.Client: {e}")
        
    # Пробуем создать клиент нового API
    try:
        client = anthropic.Anthropic(api_key=anthropic_key)
        print("Клиент anthropic.Anthropic успешно создан")
    except Exception as e:
        print(f"Ошибка при создании anthropic.Anthropic: {e}")
        
except Exception as e:
    print(f"Ошибка при импорте библиотеки anthropic: {e}")

# Проверка всех установленных пакетов
print("\nУстановленные пакеты:")
for package in pkg_resources.working_set:
    print(f"{package.key}=={package.version}") 