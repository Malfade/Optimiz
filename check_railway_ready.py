#!/usr/bin/env python
"""
Скрипт для проверки настроек проекта перед деплоем на Railway.
Запускайте его для проверки вашей конфигурации перед отправкой на Railway.
"""
import os
import sys
import importlib
import json
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("railway_check")

# Список важных файлов
REQUIRED_FILES = [
    "optimization_bot.py",
    "safe_anthropic.py",
    "anthropic_wrapper.py",
    "requirements.txt",
    "railway.json",
    "Procfile"
]

# Необходимые переменные окружения
REQUIRED_ENV_VARS = [
    "TELEGRAM_TOKEN",
    "ANTHROPIC_API_KEY"
]

# Требуемые пакеты
REQUIRED_PACKAGES = [
    "anthropic",
    "pyTelegramBotAPI",
    "python-dotenv",
    "requests"
]

def check_file_existence():
    """Проверка наличия необходимых файлов"""
    print("Проверка необходимых файлов...")
    missing_files = []
    
    for file in REQUIRED_FILES:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    else:
        print("✅ Все необходимые файлы присутствуют")
        return True

def check_env_vars():
    """Проверка переменных окружения"""
    print("\nПроверка переменных окружения...")
    # Загружаем .env файл, если он существует
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ Все необходимые переменные окружения установлены")
        return True

def check_packages():
    """Проверка установленных пакетов"""
    print("\nПроверка пакетов Python...")
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
        return False
    else:
        print("✅ Все необходимые пакеты установлены")
        return True

def check_railway_json():
    """Проверка файла railway.json"""
    print("\nПроверка файла railway.json...")
    try:
        with open("railway.json", "r") as f:
            config = json.load(f)
            
        if "deploy" in config and "startCommand" in config["deploy"]:
            command = config["deploy"]["startCommand"]
            if "safe_anthropic.py" not in command:
                print("⚠️ Команда запуска не использует safe_anthropic.py")
                return False
            else:
                print("✅ Файл railway.json настроен корректно")
                return True
        else:
            print("⚠️ В railway.json отсутствует команда запуска")
            return False
    except Exception as e:
        print(f"❌ Ошибка при чтении railway.json: {e}")
        return False

def check_anthropic_version():
    """Проверка версии библиотеки Anthropic"""
    print("\nПроверка версии библиотеки Anthropic...")
    try:
        import pkg_resources
        version = pkg_resources.get_distribution("anthropic").version
        print(f"- Установленная версия anthropic: {version}")
        
        if version != "0.19.0":
            print("⚠️ Рекомендуется использовать версию 0.19.0 вместо " + version)
            return False
        else:
            print("✅ Установлена рекомендуемая версия anthropic 0.19.0")
            return True
    except Exception as e:
        print(f"❌ Ошибка при проверке версии anthropic: {e}")
        return False

def check_anthropic_import():
    """Проверка правильного импорта anthropic"""
    print("\nПроверка импорта библиотеки Anthropic...")
    try:
        with open("optimization_bot.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "import anthropic_wrapper as anthropic" in content:
            print("✅ Правильный импорт anthropic_wrapper в optimization_bot.py")
            return True
        else:
            print("❌ В файле optimization_bot.py не используется anthropic_wrapper")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке импорта: {e}")
        return False

def check_procfile():
    """Проверка файла Procfile"""
    print("\nПроверка файла Procfile...")
    try:
        with open("Procfile", "r") as f:
            content = f.read()
            
        if "worker: python safe_anthropic.py && python optimization_bot.py" in content:
            print("✅ Procfile настроен правильно")
            return True
        else:
            print("⚠️ Procfile не использует safe_anthropic.py")
            return False
    except Exception as e:
        print(f"❌ Ошибка при чтении Procfile: {e}")
        return False

def main():
    """Основная функция проверки"""
    print("\n=== Проверка готовности к деплою на Railway ===\n")
    
    checks = [
        check_file_existence(),
        check_env_vars(),
        check_packages(),
        check_railway_json(),
        check_anthropic_version(),
        check_anthropic_import(),
        check_procfile()
    ]
    
    success_count = sum(1 for check in checks if check)
    total_checks = len(checks)
    
    print(f"\n=== Результаты проверки: {success_count}/{total_checks} ===")
    
    if all(checks):
        print("\n✅ Конфигурация готова к деплою на Railway!")
    else:
        print("\n⚠️ Исправьте указанные проблемы перед деплоем на Railway")
    
    return 0 if all(checks) else 1

if __name__ == "__main__":
    sys.exit(main()) 