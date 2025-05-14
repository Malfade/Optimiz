#!/usr/bin/env python
"""
Инструмент для проверки и исправления инфраструктуры бота на Railway.
Проверяет API ключи, переменные окружения и совместимость библиотек.
"""

import os
import sys
import re
import asyncio
import logging
import pkg_resources
import json
from dotenv import load_dotenv, set_key

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("railway_fix")

def check_environment():
    """
    Проверяет, запущен ли скрипт в Railway
    
    Returns:
        bool: True если скрипт запущен в Railway
    """
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    if railway_env:
        logger.info(f"Скрипт запущен в Railway, окружение: {railway_env}")
        return True
    else:
        logger.info("Скрипт запущен в локальном окружении")
        return False

def check_railway_json():
    """
    Проверяет настройки в файле railway.json
    
    Returns:
        tuple: (bool, dict) - успех проверки и данные из файла
    """
    try:
        if not os.path.exists('railway.json'):
            logger.error("Файл railway.json не найден")
            return False, {}
        
        with open('railway.json', 'r') as f:
            data = json.load(f)
        
        logger.info("Файл railway.json успешно загружен")
        
        # Проверка важных параметров
        if 'deploy' not in data:
            logger.error("В файле railway.json отсутствует секция 'deploy'")
            return False, data
        
        # Проверка количества инстансов
        if 'numInstances' not in data['deploy']:
            logger.warning("В файле railway.json не задано количество инстансов")
        elif data['deploy']['numInstances'] != 1:
            logger.warning(f"Настроено {data['deploy']['numInstances']} инстансов, рекомендуется установить 1")
        else:
            logger.info("Количество инстансов установлено правильно (1)")
        
        # Проверка команды запуска
        if 'startCommand' not in data['deploy']:
            logger.error("В файле railway.json не задана команда запуска")
        elif 'test_api_key.py' not in data['deploy']['startCommand']:
            logger.warning("Команда запуска не включает проверку API ключа")
        else:
            logger.info("Команда запуска настроена правильно")
        
        return True, data
    except Exception as e:
        logger.error(f"Ошибка при проверке railway.json: {e}")
        return False, {}

def check_requirements():
    """
    Проверяет версии библиотек в requirements.txt
    
    Returns:
        tuple: (bool, dict) - успех проверки и данные о библиотеках
    """
    libraries = {}
    issues = []
    
    try:
        if not os.path.exists('requirements.txt'):
            logger.error("Файл requirements.txt не найден")
            return False, {}
        
        # Читаем requirements.txt
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Извлекаем имя библиотеки и версию
            if '==' in line:
                name, version = line.split('==', 1)
                libraries[name.strip()] = version.strip()
            elif '>=' in line:
                name, version = line.split('>=', 1)
                libraries[name.strip()] = f">={version.strip()}"
        
        # Проверяем наличие и версию ключевых библиотек
        if 'anthropic' not in libraries:
            issues.append("Библиотека anthropic не указана в requirements.txt")
        else:
            anthropic_version = libraries['anthropic']
            
            # Проверяем установленную версию
            installed_version = None
            try:
                installed_version = pkg_resources.get_distribution("anthropic").version
                logger.info(f"Установлена библиотека anthropic версии {installed_version}")
                
                # Несоответствие версий
                if '==' in anthropic_version and installed_version != anthropic_version.replace('==', ''):
                    issues.append(f"Установленная версия anthropic ({installed_version}) "
                                  f"не соответствует указанной в requirements.txt ({anthropic_version})")
            except:
                issues.append("Не удалось определить установленную версию anthropic")
            
            # Рекомендации по версии библиотеки
            if '0.5.0' in anthropic_version or '0.3' in anthropic_version:
                logger.info(f"Используется стабильная версия anthropic: {anthropic_version}")
            elif '0.51.' in anthropic_version or '0.6' in anthropic_version or '0.7' in anthropic_version:
                logger.info(f"Используется новая версия anthropic: {anthropic_version}")
                logger.warning("Новые версии требуют ключ в формате sk-ant-api03-...")
            else:
                issues.append(f"Неизвестная версия anthropic: {anthropic_version}")
                
        # Проверяем другие важные библиотеки
        required_libraries = ['telebot', 'requests', 'python-dotenv']
        for lib in required_libraries:
            if lib not in libraries:
                issues.append(f"Библиотека {lib} не указана в requirements.txt")
        
        # Выводим результаты
        if issues:
            logger.warning("Обнаружены проблемы в requirements.txt:")
            for issue in issues:
                logger.warning(f"- {issue}")
            return False, libraries
        else:
            logger.info("Проверка requirements.txt завершена успешно")
            return True, libraries
    except Exception as e:
        logger.error(f"Ошибка при проверке requirements.txt: {e}")
        return False, {}

async def check_api_key():
    """
    Проверяет API ключ Anthropic
    
    Returns:
        tuple: (bool, str) - успех проверки и сообщение
    """
    try:
        # Импортируем вспомогательный модуль
        from anthropic_helper import get_api_key_with_prefix, create_anthropic_client, is_valid_anthropic_key
        
        # Получаем API ключ
        api_key = get_api_key_with_prefix()
        
        if not api_key:
            logger.error("API ключ не найден в переменных окружения")
            return False, "API ключ не найден"
        
        # Проверка формата ключа
        if not is_valid_anthropic_key(api_key):
            logger.warning(f"API ключ не соответствует ожидаемому формату")
            formatted_key = None
            
            # Попытка форматирования ключа
            if not api_key.startswith("sk-ant-api03-") and not api_key.startswith("sk-"):
                # Ключ без префикса
                formatted_key = f"sk-ant-api03-{api_key}"
                logger.info(f"Сформирован API ключ с префиксом sk-ant-api03-")
            elif api_key.startswith("sk-") and not api_key.startswith("sk-ant-api"):
                # Ключ со старым префиксом
                formatted_key = api_key.replace("sk-", "sk-ant-api03-")
                logger.info(f"Сформирован API ключ из старого формата в новый")
            
            if formatted_key and is_valid_anthropic_key(formatted_key):
                # Обновляем ключ в .env
                try:
                    env_path = ".env"
                    if os.path.exists(env_path):
                        set_key(env_path, "ANTHROPIC_API_KEY", formatted_key)
                        logger.info(f"API ключ обновлен в файле .env")
                        # Перезагружаем ключ
                        api_key = formatted_key
                except Exception as e:
                    logger.error(f"Ошибка при обновлении API ключа в .env: {e}")
        
        # Создаем клиент
        client, method, error = await create_anthropic_client()
        
        if error:
            logger.error(f"Ошибка создания клиента: {error}")
            return False, f"Ошибка API: {error}"
        
        logger.info(f"Клиент успешно создан, используется метод: {method}")
        
        # Тестируем клиент минимальным запросом
        try:
            if method == "completion":
                # Старое API
                response = client.completion(
                    prompt="\n\nHuman: Привет!\n\nAssistant:",
                    model="claude-instant-1.2",
                    max_tokens_to_sample=5,
                    temperature=0
                )
                result = response.completion
            else:
                # Новое API
                messages = [
                    {
                        "role": "user", 
                        "content": "Привет!"
                    }
                ]
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=5,
                    temperature=0,
                    messages=messages
                )
                result = response.content[0].text
            
            logger.info(f"Тестовый запрос выполнен успешно")
            return True, "API ключ полностью функционален"
        except Exception as e:
            error_str = str(e)
            logger.error(f"Ошибка при выполнении тестового запроса: {e}")
            
            if "invalid x-api-key" in error_str or "authentication_error" in error_str:
                return False, "Ошибка аутентификации: неверный API ключ"
            elif "credit balance is too low" in error_str:
                return False, "Недостаточно средств на балансе API"
            else:
                return False, f"Ошибка API: {e}"
    except Exception as e:
        logger.error(f"Ошибка при проверке API ключа: {e}")
        return False, f"Ошибка проверки: {e}"

def check_telegram_token():
    """
    Проверяет токен Telegram бота
    
    Returns:
        tuple: (bool, str) - успех проверки и сообщение
    """
    try:
        import telebot
        
        # Получаем токен
        token = os.getenv('TELEGRAM_TOKEN')
        
        if not token:
            logger.error("Токен Telegram бота не найден в переменных окружения")
            return False, "Токен не найден"
        
        # Проверяем формат токена (примерно)
        if not re.match(r'^[0-9]{8,}:[\w-]{35,}$', token):
            logger.warning("Формат токена Telegram может быть некорректным")
        
        # Проверяем токен через API
        try:
            bot = telebot.TeleBot(token)
            bot_info = bot.get_me()
            logger.info(f"Успешное подключение к боту: @{bot_info.username} (ID: {bot_info.id})")
            return True, f"Токен действителен, бот: @{bot_info.username}"
        except Exception as e:
            logger.error(f"Ошибка при проверке токена Telegram: {e}")
            return False, f"Ошибка Telegram API: {e}"
    except Exception as e:
        logger.error(f"Ошибка при проверке токена Telegram: {e}")
        return False, f"Ошибка проверки: {e}"

def fix_railway_json(data):
    """
    Исправляет файл railway.json при необходимости
    
    Args:
        data: текущие данные из файла
        
    Returns:
        bool: True если файл был исправлен успешно
    """
    try:
        needs_update = False
        
        # Проверяем и создаем структуру файла
        if 'deploy' not in data:
            data['deploy'] = {}
            needs_update = True
        
        # Устанавливаем numInstances = 1
        if 'numInstances' not in data['deploy'] or data['deploy']['numInstances'] != 1:
            data['deploy']['numInstances'] = 1
            needs_update = True
        
        # Проверяем команду запуска
        if 'startCommand' not in data['deploy']:
            data['deploy']['startCommand'] = "python test_api_key.py && python optimization_bot.py"
            needs_update = True
        elif 'test_api_key.py' not in data['deploy']['startCommand']:
            data['deploy']['startCommand'] = "python test_api_key.py && python optimization_bot.py"
            needs_update = True
        
        # Проверяем политику перезапуска
        if 'restartPolicyType' not in data['deploy']:
            data['deploy']['restartPolicyType'] = "ON_FAILURE"
            data['deploy']['restartPolicyMaxRetries'] = 5
            data['deploy']['restartPolicyBackoffSeconds'] = 30
            needs_update = True
        
        # Записываем изменения
        if needs_update:
            with open('railway.json', 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Файл railway.json успешно обновлен")
            return True
        else:
            logger.info("Файл railway.json не требует обновления")
            return False
    except Exception as e:
        logger.error(f"Ошибка при исправлении railway.json: {e}")
        return False

async def main():
    """
    Основная функция скрипта
    """
    print("\n========== ПРОВЕРКА ИНФРАСТРУКТУРЫ БОТА НА RAILWAY ==========")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем окружение
    is_railway = check_environment()
    
    # Собираем результаты проверок
    results = {
        "railway_json": None,
        "requirements": None,
        "api_key": None,
        "telegram_token": None
    }
    
    # Проверяем railway.json
    success, data = check_railway_json()
    results["railway_json"] = {"success": success, "data": data}
    
    # Проверяем requirements.txt
    success, libraries = check_requirements()
    results["requirements"] = {"success": success, "libraries": libraries}
    
    # Проверяем API ключ Anthropic
    success, message = await check_api_key()
    results["api_key"] = {"success": success, "message": message}
    
    # Проверяем токен Telegram
    success, message = check_telegram_token()
    results["telegram_token"] = {"success": success, "message": message}
    
    # Подсчитываем количество проблем
    issue_count = sum(1 for key, value in results.items() if value and not value.get("success", False))
    
    # Выводим сводную информацию
    print("\n========== РЕЗУЛЬТАТЫ ПРОВЕРКИ ==========")
    print(f"🔶 Обнаружено проблем: {issue_count}")
    print(f"🔶 Railway.json: {'✅ OK' if results['railway_json']['success'] else '❌ Требуется исправление'}")
    print(f"🔶 Requirements.txt: {'✅ OK' if results['requirements']['success'] else '❌ Требуется исправление'}")
    print(f"🔶 API ключ Anthropic: {'✅ OK' if results['api_key']['success'] else '❌ Требуется исправление'}")
    print(f"🔶 Токен Telegram: {'✅ OK' if results['telegram_token']['success'] else '❌ Требуется исправление'}")
    
    # Проводим автоматические исправления
    if not results['railway_json']['success']:
        if fix_railway_json(results['railway_json']['data']):
            print("✅ Файл railway.json успешно исправлен")
        else:
            print("❌ Не удалось исправить railway.json")
    
    # Рекомендации
    if issue_count > 0:
        print("\n========== РЕКОМЕНДАЦИИ ==========")
        
        if not results['api_key']['success']:
            print("1. Обновите API ключ Anthropic:")
            print("   - Используйте утилиту update_api_key.py")
            print("   - Убедитесь, что формат ключа соответствует версии библиотеки")
            
            anthropic_version = None
            if results['requirements']['libraries'].get('anthropic'):
                anthropic_version = results['requirements']['libraries']['anthropic']
            
            if anthropic_version and ('0.51' in anthropic_version or '0.6' in anthropic_version or '0.7' in anthropic_version):
                print("   - Для версии библиотеки", anthropic_version, "требуется ключ формата sk-ant-api03-...")
            elif anthropic_version:
                print("   - Для версии библиотеки", anthropic_version, "требуется ключ формата sk-...")
        
        if not results['telegram_token']['success']:
            print("2. Проверьте токен Telegram бота:")
            print("   - Токен должен быть указан в переменной TELEGRAM_TOKEN")
            print("   - Получите новый токен у @BotFather если необходимо")
        
        if is_railway:
            print("3. Для Railway:")
            print("   - Остановите все текущие экземпляры бота")
            print("   - Обновите переменные окружения в панели Railway")
            print("   - Перезапустите развертывание")
    else:
        print("\n✅ Все проверки пройдены успешно. Инфраструктура готова к работе.")
    
    print("\n==============================================")

if __name__ == "__main__":
    asyncio.run(main()) 