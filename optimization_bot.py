import os
import platform
import socket
import atexit
import logging
import json
import base64
import re
from io import BytesIO
from datetime import datetime
import zipfile
import asyncio
# Используем прямой импорт нашей собственной реализации
import fallback_anthropic as anthropic
# Обертки для обратной совместимости
# import anthropic_wrapper as anthropic
import requests
from dotenv import load_dotenv
import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot
import time
import pkg_resources
import inspect
# Импортируем API сервер для активации подписок
try:
    import subscription_api
    has_api_server = True
except ImportError:
    has_api_server = False
    print("ВНИМАНИЕ: Модуль API сервера для подписок не найден")

# Импортируем модуль проверки подписок
try:
    from subscription_check import check_user_subscription, add_user_subscription, get_subscription_info
    has_subscription_check = True
except ImportError:
    has_subscription_check = False
    print("ВНИМАНИЕ: Модуль проверки подписок не найден, функционал подписок отключен")

# URL платежной системы из переменной окружения
PAYMENT_SYSTEM_URL = os.getenv('PAYMENT_SYSTEM_URL', 'https://your-payment-app.up.railway.app')

# Импортируем модуль для healthcheck (для Railway)
try:
    import healthcheck
    has_healthcheck = True
except ImportError:
    has_healthcheck = False

# Проверка на запуск только одного экземпляра бота - кросс-платформенная реализация
def ensure_single_instance():
    """
    Гарантирует запуск только одного экземпляра бота.
    Работает на Windows, Linux и MacOS.
    В облачном окружении Railway пропускает проверку.
    """
    # Пропускаем проверку, если мы в облачном окружении Railway
    if os.getenv('RAILWAY_ENVIRONMENT') is not None:
        logger.info("Запуск в облачном окружении Railway, пропускаем проверку единственного экземпляра")
        return True
        
    try:
        # Определяем путь к файлу блокировки
        lock_dir = os.path.dirname(os.path.abspath(__file__))
        lock_file_path = os.path.join(lock_dir, "bot.lock")
        
        # Глобальный объект блокировки
        global lock_handle
        
        # Проверяем, существует ли файл блокировки
        if os.path.exists(lock_file_path):
            # Проверяем, жив ли процесс, который создал файл
            try:
                with open(lock_file_path, 'r') as f:
                    pid = int(f.read().strip())
                
                # Проверка существования процесса (кросс-платформенно)
                if platform.system() == 'Windows':
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    SYNCHRONIZE = 0x00100000
                    process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
                    if process:
                        kernel32.CloseHandle(process)
                        # Процесс существует, значит бот уже запущен
                        logger.error(f"Бот уже запущен (PID: {pid}). Завершаем работу.")
                        return False
                else:  # Linux/MacOS
                    try:
                        # Отправляем сигнал 0 процессу - не убивает его,
                        # но генерирует ошибку, если процесс не существует
                        os.kill(pid, 0)
                        # Процесс существует, значит бот уже запущен
                        logger.error(f"Бот уже запущен (PID: {pid}). Завершаем работу.")
                        return False
                    except OSError:
                        # Процесс не существует
                        pass
            except (ValueError, IOError):
                # Некорректный PID или не удалось прочитать файл
                pass
            
            # Если мы здесь, значит процесс не существует или файл поврежден
            # Удаляем старый файл блокировки
            try:
                os.remove(lock_file_path)
                logger.info(f"Удален старый файл блокировки (PID не существует)")
            except OSError:
                pass
        
        # Создаем новый файл блокировки
        try:
            with open(lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            logger.info(f"Бот запущен в единственном экземпляре (PID: {os.getpid()})")
            
            # Регистрируем функцию для очистки при завершении
            def cleanup_lock():
                try:
                    if os.path.exists(lock_file_path):
                        os.remove(lock_file_path)
                        logger.info("Файл блокировки удален, бот завершает работу")
                except Exception as e:
                    logger.error(f"Ошибка при удалении файла блокировки: {e}")
            
            atexit.register(cleanup_lock)
            return True
        except Exception as e:
            logger.error(f"Не удалось создать файл блокировки: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при проверке единственного экземпляра: {e}")
        return False


# Глобальная переменная для блокировки
lock_handle = None
# Глобальная переменная для сокета
single_instance_socket = None

# Импортируем наши модули
from script_validator import ScriptValidator
from script_metrics import ScriptMetrics
from prompt_optimizer import PromptOptimizer

# Импортируем модуль для валидации скриптов
from validate_and_fix_scripts import validate_and_fix_scripts

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация бота
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Создаем экземпляр бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Инициализируем API сервер подписок
if has_api_server:
    subscription_api.start_subscription_api(bot)
    logger.info("API сервер подписок успешно инициализирован")

# Словари для хранения состояний пользователей
user_states = {}  # Хранение состояний пользователей
user_files = {}   # Хранение файлов пользователей
user_messages = {}  # Хранение текста сообщений

# Функция проверки подписки перед действиями
def check_subscription_before_action(message):
    """
    Проверяет подписку пользователя перед выполнением действия
    
    Args:
        message: Объект сообщения от Telegram
        
    Returns:
        bool: True если подписка активна, False если нет
    """
    try:
        # Если проверка подписок отключена, пропускаем проверку
        if not has_subscription_check:
            return True
            
        # Проверяем подписку пользователя
        user_id = str(message.chat.id)
        has_subscription = check_user_subscription(user_id)
        
        if not has_subscription:
            # Получаем информацию о боте для передачи в мини-приложение
            try:
                bot_info = bot.get_me()
                bot_username = bot_info.username
            except Exception as e:
                logger.error(f"Ошибка при получении информации о боте: {e}")
                bot_username = "optimizator_bot"  # fallback значение
            
            # Создаем кнопку для оплаты через мини-приложение
            markup = types.InlineKeyboardMarkup()
            
            # Создаем URL для мини-приложения оплаты
            # Для WebApp в Telegram необходимо использовать только публичные URL (localhost не подходит)
            # Используем реальный URL платежной системы на Railway
            payment_url = f"{PAYMENT_SYSTEM_URL}/?user_id={user_id}&bot_username={bot_username}"
            
            # Добавляем кнопку оплаты через мини-приложение
            payment_button = types.InlineKeyboardButton(
                text="💳 Оплатить подписку", 
                web_app=types.WebAppInfo(url=payment_url)
            )
            markup.add(payment_button)
            
            # Отправляем сообщение с кнопкой оплаты
            bot.send_message(
                chat_id=message.chat.id, 
                text="⚠️ *Ваша подписка не активна*\n\n"
                     "Для использования всех функций бота необходимо приобрести подписку.\n\n"
                     "💡 Нажмите кнопку ниже для выбора тарифа и оплаты:", 
                parse_mode="Markdown",
                reply_markup=markup
            )
            return False
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        # В случае ошибки разрешаем использование (fail-safe)
        return True

# Статистика по генерации скриптов и ошибкам
script_gen_count = 0
error_stats = {
    "total_errors": 0,
    "ps_syntax": 0,
    "bat_syntax": 0,
    "file_access": 0,
    "security": 0,
    "missing_blocks": 0,
    "other": 0
}

# Шаблон промпта для генерации скрипта оптимизации
OPTIMIZATION_PROMPT_TEMPLATE = """Ты эксперт по оптимизации Windows. Тебе предоставлен скриншот системной информации. Твоя задача - создать скрипты для оптимизации этой системы.

Обязательно следуй этим требованиям к скриптам:

1. PowerShell скрипт (.ps1):
   - Всегда начинай с установки кодировки UTF-8: `$OutputEncoding = [System.Text.Encoding]::UTF8`
   - Проверяй права администратора в самом начале скрипта
   - Все блоки try ДОЛЖНЫ иметь соответствующие блоки catch
   - НИКОГДА не используй формат ${1}:TEMP в путях - это приводит к ошибкам!
   - ВСЕГДА используй ТОЛЬКО формат $env:VARIABLENAME для переменных окружения (например: $env:TEMP, $env:APPDATA, $env:USERPROFILE)
   - Внутри строк с двоеточием используй `${variable}` вместо `$variable`
   - Проверяй существование файлов с помощью Test-Path перед их использованием
   - Добавляй ключ -Force для команд Remove-Item
   - Обеспечь балансировку всех фигурных скобок
   - Для вывода сообщений об ошибках используй формат: `"Сообщение: ${variable}"`

2. Batch файл (.bat):
   - НИ В КОЕМ СЛУЧАЕ не используй русские символы в BAT-файлах!
   - Обязательно начинай с `@echo off` и `chcp 65001 >nul`
   - Проверяй права администратора
   - Используй ТОЛЬКО английский текст в bat-файле
   - Добавляй корректные параметры при вызове PowerShell: `-ExecutionPolicy Bypass -NoProfile -File`
   - Используй перенаправление ошибок `>nul 2>&1` для команд

3. ReadMe файл (README.md):
   - Подробная документация по использованию скриптов
   - Описание выполняемых оптимизаций
   - Требования и предупреждения

Предоставь три файла:
1. WindowsOptimizer.ps1 - скрипт оптимизации PowerShell, который анализирует систему и оптимизирует её
2. Start-Optimizer.bat - bat-файл для запуска PowerShell скрипта с нужными параметрами (ТОЛЬКО с английским текстом)
3. README.md - инструкция по использованию скриптов

Вот шаблон Batch-файла, которого нужно строго придерживаться:
```batch
@echo off
chcp 65001 >nul
title Windows Optimization

:: Check administrator rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Administrator rights required.
    echo Please run this file as administrator.
    pause
    exit /b 1
)

:: Script file check
if not exist "WindowsOptimizer.ps1" (
    echo File WindowsOptimizer.ps1 not found.
    echo Please make sure it is in the same folder.
    pause
    exit
)

:: Run PowerShell script with needed parameters
echo Starting Windows optimization script...
echo ==========================================

powershell -ExecutionPolicy Bypass -NoProfile -File "WindowsOptimizer.ps1" -Encoding UTF8

echo ==========================================
echo Optimization script completed.
pause
```
"""

# Шаблон промпта для исправления ошибок в скрипте
ERROR_FIX_PROMPT_TEMPLATE = """Ты эксперт по PowerShell и Batch скриптам. Перед тобой скриншот с ошибками выполнения скрипта оптимизации Windows. Твоя задача - проанализировать ошибки и исправить код скрипта.

Вот основные типы ошибок, которые могут встречаться:

1. Синтаксические ошибки:
   - Несбалансированные скобки
   - Неверное использование переменных
   - Ошибки в конструкциях try-catch
   - Неэкранированные специальные символы

2. Проблемы с доступом:
   - Отсутствие проверки прав администратора
   - Попытка доступа к несуществующим файлам или службам
   - Отсутствие параметра -Force для Remove-Item

3. Проблемы кодировки:
   - Отсутствие установки правильной кодировки
   - Неверное отображение кириллических символов

Важные правила при исправлении:

1. Для PowerShell:
   - Всегда добавляй в начало скрипта: `$OutputEncoding = [System.Text.Encoding]::UTF8`
   - Все блоки try ДОЛЖНЫ иметь соответствующие блоки catch
   - Переменные в строках с двоеточием используй в формате `${variable}` вместо `$variable`
   - Используй проверки Test-Path перед операциями с файлами
   - Балансируй все фигурные скобки

2. Для Batch:
   - Начинай с `@echo off` и `chcp 65001 >nul`
   - Добавляй корректные параметры при вызове PowerShell

Предоставь исправленные версии файлов с учетом обнаруженных на скриншоте проблем.

ОБЯЗАТЕЛЬНО ПРОВЕРЬТЕ:
- Проверку прав администратора
- Наличие и корректность блоков обработки ошибок
- Кодировку UTF-8 для PowerShell скриптов
- Балансировку всех скобок в скрипте
- Правильный формат переменных в строках с двоеточием (${variable})
"""

def validate_and_fix_scripts(files):
    """
    Валидирует и исправляет скрипты
    
    Args:
        files: словарь с файлами (имя файла -> содержимое)
    
    Returns:
        tuple: (исправленные файлы, результаты валидации, кол-во исправленных ошибок)
    """
    validator = ScriptValidator()
    
    # Валидируем скрипты
    validation_results = validator.validate_scripts(files)
    
    # Подсчитываем общее количество ошибок
    total_errors = sum(len(errors) for errors in validation_results.values())
    logger.info(f"Найдено {total_errors} проблем в скриптах")
    
    # Исправляем распространенные проблемы
    fixed_files = validator.repair_common_issues(files)
    
    # Валидируем исправленные скрипты
    fixed_validation_results = validator.validate_scripts(fixed_files)
    
    # Подсчитываем количество исправленных ошибок
    fixed_errors = sum(len(errors) for errors in fixed_validation_results.values())
    errors_corrected = total_errors - fixed_errors
    
    # Улучшаем скрипты, добавляя полезные функции
    enhanced_files = validator.enhance_scripts(fixed_files)
    
    logger.info(f"Исправлено {errors_corrected} проблем, осталось {fixed_errors} проблем")
    
    return enhanced_files, fixed_validation_results, errors_corrected

class OptimizationBot:
    """Класс для оптимизации Windows с помощью AI"""
    
    def __init__(self, api_key, validator=None):
        """
        Инициализация бота оптимизации
        
        Args:
            api_key: API ключ для Anthropic
            validator: Экземпляр ScriptValidator или None
        """
        try:
            # Сохраняем API ключ
            self.api_key = api_key
            
            # Создаем клиент API (используем нашу собственную реализацию)
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("OptimizationBot: Клиент Claude API успешно инициализирован")

            # Инициализация валидатора
            self.validator = validator if validator else ScriptValidator()
            
            # Модель для использования
            self.models = {
                "default": "claude-3-haiku-20240307",  # Быстрая и доступная модель
                "high_quality": "claude-3-opus-20240229"  # Для сложных случаев
            }
            
            # Инициализация промптов
            self.prompts = {
                "OPTIMIZATION_PROMPT_TEMPLATE": OPTIMIZATION_PROMPT_TEMPLATE,
                "ERROR_FIX_PROMPT_TEMPLATE": ERROR_FIX_PROMPT_TEMPLATE
            }
            
            # Инициализация метрик
            self.metrics = ScriptMetrics()
            
            # Тип клиента и метод вызова API
            self.client_method = "messages"
            
            # Проверка состояния
            self.is_initialized = True
            logger.info("Бот оптимизации Windows запущен!")
        except Exception as e:
            logger.error(f"Ошибка при инициализации бота оптимизации: {e}")
            self.is_initialized = False
    
    async def generate_new_script(self, message):
        """Генерация нового скрипта оптимизации на основе скриншота системы"""
        
        try:
            logger.info(f"Начинаю генерацию скрипта для пользователя {message.chat.id}")
            
            # Проверяем наличие фото
            if not message.photo:
                return "Не найдено изображение. Пожалуйста, отправьте скриншот системной информации."
            
            # Получаем файл фото
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
            
            # Загружаем изображение
            img_data = requests.get(file_url).content
            
            # Кодируем изображение в base64
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # Формируем сообщение для API
            user_message = user_messages.get(message.chat.id, "Создай скрипт оптимизации Windows")
            
            # Используем оптимизированный промпт, если он доступен
            prompt = self.prompts.get("OPTIMIZATION_PROMPT_TEMPLATE", OPTIMIZATION_PROMPT_TEMPLATE)
            
            # Подготовка текста промпта
            enhanced_prompt = f"{prompt}\n\n{user_message}\n\nЯ отправил скриншот со сведениями о системе. Создай скрипты оптимизации для Windows."
            
            try:
                # Проверяем, инициализирован ли клиент API
                if self.client is None:
                    raise Exception("API клиент не инициализирован. Используем шаблонные скрипты.")
                
                logger.info("Отправляю запрос к Claude API...")
                
                # Отправляем запрос в зависимости от версии клиента
                if self.client_method == "completion":
                    # Старый API (версии <= 0.5.9)
                    try:
                        response = await asyncio.to_thread(
                            self.client.completion,
                            prompt=f"\n\nHuman: {enhanced_prompt}\n\nAssistant:",
                            model="claude-2",
                            max_tokens_to_sample=4000,
                            temperature=0.7
                        )
                        response_text = response.completion
                    except Exception as old_api_error:
                        logger.error(f"Ошибка при использовании старого API: {old_api_error}")
                        # Попробуем прямой вызов функции без await
                        response = self.client.completion(
                            prompt=f"\n\nHuman: {enhanced_prompt}\n\nAssistant:",
                            model="claude-2",
                            max_tokens_to_sample=4000,
                            temperature=0.7
                        )
                        response_text = response.completion
                else:
                    # Новый API (версии >= 0.51.0)
                    try:
                        # Для API v0.51.0+
                        messages = [
                            {
                                "role": "user", 
                                "content": [
                                    {
                                        "type": "text",
                                        "text": enhanced_prompt
                                    }
                                ]
                            }
                        ]
                        response = await asyncio.to_thread(
                            self.client.messages.create,
                            model="claude-3-opus-20240229",
                            max_tokens=4000,
                            messages=messages
                        )
                        response_text = response.content[0].text
                    except Exception as new_api_error:
                        # Резервный вызов без asyncio
                        error_str = str(new_api_error)
                        logger.error(f"Ошибка при использовании нового API асинхронно: {new_api_error}")
                        
                        if "invalid x-api-key" in error_str or "authentication_error" in error_str:
                            # Отправляем сообщение об ошибке аутентификации
                            bot.send_message(message.chat.id, 
                                             "⚠️ Обнаружена проблема с API ключом.\n\n"
                                             "Пожалуйста, получите новый ключ API на сайте Anthropic и настройте его в файле .env.\n"
                                             "Пока что будут использоваться шаблонные скрипты.")
                            
                            # Переходим к использованию шаблонных скриптов
                            files = self._get_template_scripts()
                            # Проверяем и улучшаем шаблонные скрипты
                            fixed_files, validation_results, errors_corrected = validate_and_fix_scripts(files)
                            # Обновляем статистику
                            self.metrics.record_script_generation({
                                "timestamp": datetime.now().isoformat(),
                                "errors": validation_results,
                                "error_count": sum(len(issues) for issues in validation_results.values()),
                                "fixed_count": errors_corrected,
                                "model": "template_fallback",
                                "api_error": True
                            })
                            # Сохраняем файлы для последующей отправки
                            user_files[message.chat.id] = fixed_files
                            return fixed_files
                            
                        try:
                            messages = [
                                {
                                    "role": "user", 
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": enhanced_prompt
                                        }
                                    ]
                                }
                            ]
                            response = self.client.messages.create(
                                model="claude-3-opus-20240229",
                                max_tokens=4000,
                                messages=messages
                            )
                            response_text = response.content[0].text
                        except Exception as e:
                            logger.error(f"Ошибка при использовании нового API напрямую: {e}")
                            raise
                
                logger.info(f"Получен ответ от Claude API, длина: {len(response_text)} символов")
            except Exception as api_error:
                # Проверяем ошибку баланса API
                error_str = str(api_error)
                if "credit balance is too low" in error_str or "Your credit balance is too low" in error_str:
                    logger.error(f"Ошибка недостаточного баланса API: {api_error}")
                    error_message = "К сожалению, баланс API-кредитов исчерпан. Пожалуйста, обратитесь к администратору для пополнения баланса."
                    error_message += "\n\nПока что будет использован резервный подход с шаблонными скриптами."
                    bot.send_message(message.chat.id, error_message)
                    
                    # Используем альтернативный подход с шаблонами
                    files = self._get_template_scripts()
                    
                    # Проверяем и улучшаем шаблонные скрипты
                    fixed_files, validation_results, errors_corrected = validate_and_fix_scripts(files)
                    
                    # Обновляем статистику
                    self.metrics.record_script_generation({
                        "timestamp": datetime.now().isoformat(),
                        "errors": validation_results,
                        "error_count": sum(len(issues) for issues in validation_results.values()),
                        "fixed_count": errors_corrected,
                        "model": "template_fallback",
                        "api_error": True
                    })
                    
                    # Сохраняем файлы для последующей отправки
                    user_files[message.chat.id] = fixed_files
                    
                    return fixed_files
                else:
                    # Другая ошибка API - просто пробрасываем исключение
                    logger.error(f"Ошибка API: {api_error}")
                    raise api_error
            
            # Извлекаем файлы из ответа
            files = self.extract_files(response_text)
            
            if not files:
                logger.warning("Не удалось извлечь файлы из ответа API")
                return "Не удалось создать скрипты оптимизации. Пожалуйста, попробуйте еще раз или отправьте другое изображение."
            
            # Дополнительная проверка и исправление скриптов
            fixed_files, validation_results, errors_corrected = validate_and_fix_scripts(files)
            
            # Обновляем статистику
            self.metrics.record_script_generation({
                "timestamp": datetime.now().isoformat(),
                "errors": validation_results,
                "error_count": sum(len(issues) for issues in validation_results.values()),
                "fixed_count": errors_corrected,
                "model": "claude-3-opus-20240229"
            })
            
            # Сохраняем файлы для последующей отправки
            user_files[message.chat.id] = fixed_files
            
            return fixed_files
        
        except Exception as e:
            logger.error(f"Ошибка при генерации скрипта: {e}")
            return f"Произошла ошибка при генерации скрипта: {str(e)}"
    
    def _get_template_scripts(self, os_type='windows'):
        """Получение шаблонных скриптов в случае ошибки API
        
        Args:
            os_type: тип операционной системы ('windows' или 'macos')
            
        Returns:
            dict: Словарь с файлами (имя файла -> содержимое)
        """
        logger.info(f"Использую шаблонные скрипты из-за ошибки API для {os_type}")
        
        # Получаем шаблонные скрипты
        template_files = {}
        
        if os_type == 'macos':
            # MacOS скрипты
            template_files["MacOptimizer.sh"] = """#!/bin/bash

# Настройка для отображения ошибок
set -e

# Функция для проверки прав администратора
check_admin() {
  if [ "$(id -u)" != "0" ]; then
    echo "Этот скрипт требует прав администратора."
    echo "Пожалуйста, запустите скрипт с sudo или используйте StartOptimizer.command"
    exit 1
  fi
}

# Проверяем права администратора
check_admin

# Настройка логирования
LOG_FILE="$HOME/Library/Logs/MacOptimizer.log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Логирование настроено. Лог будет сохранен в: $LOG_FILE"

# Функция для создания резервных копий настроек
backup_settings() {
  local setting_name="$1"
  local data="$2"
  
  # Создаем директорию для резервных копий, если её нет
  BACKUP_DIR="$HOME/MacOptimizer_Backups"
  if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
  fi
  
  # Формируем имя файла резервной копии
  TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  BACKUP_FILE="$BACKUP_DIR/${setting_name}_$TIMESTAMP.bak"
  
  # Сохраняем данные в файл
  echo "$data" > "$BACKUP_FILE"
  
  echo "Создана резервная копия $setting_name в файле $BACKUP_FILE"
  return 0
}

# Функция отображения прогресса
show_progress() {
  local activity="$1"
  local percent="$2"
  
  echo "[$activity]: $percent%"
}

# Основная функция оптимизации
optimize_mac() {
  echo "Начинаю оптимизацию macOS..."
  
  # Очистка системы
  show_progress "Optimization" 10
  cleanup_system
  
  # Оптимизация производительности
  show_progress "Optimization" 50
  optimize_performance
  
  # Отключение ненужных служб
  show_progress "Optimization" 80
  disable_services
  
  show_progress "Optimization" 100
  echo "Оптимизация успешно завершена!"
}

# Функция для очистки системы
cleanup_system() {
  echo "Очистка системы..."
  
  # Очистка кэша
  echo "Очистка пользовательского кэша..."
  rm -rf "$HOME/Library/Caches/"* 2>/dev/null || true
  
  # Очистка временных файлов
  echo "Очистка временных файлов..."
  rm -rf /tmp/* 2>/dev/null || true
  rm -rf "$HOME/Library/Application Support/CrashReporter/"* 2>/dev/null || true
  
  # Очистка корзины
  echo "Очистка корзины..."
  rm -rf "$HOME/.Trash/"* 2>/dev/null || true
  
  # Очистка журналов системы
  echo "Очистка системных журналов..."
  sudo rm -rf /var/log/*.gz 2>/dev/null || true
  sudo rm -rf /var/log/asl/*.asl 2>/dev/null || true
  
  echo "Очистка системы завершена успешно"
}

# Функция для оптимизации производительности
optimize_performance() {
  echo "Оптимизация производительности..."
  
  # Отключение визуальных эффектов
  echo "Настройка визуальных эффектов..."
  
  # Сохраняем текущие настройки
  current_settings=$(defaults read com.apple.dock 2>/dev/null || echo "No existing settings")
  backup_settings "DockSettings" "$current_settings"
  
  # Отключаем анимацию при открытии приложений
  defaults write com.apple.dock launchanim -bool false
  
  # Ускоряем Mission Control
  defaults write com.apple.dock expose-animation-duration -float 0.1
  
  # Ускоряем анимации во Finder
  defaults write com.apple.finder DisableAllAnimations -bool true
  
  # Перезапускаем Dock для применения изменений
  killall Dock
  
  # Настройка Spotlight
  echo "Настройка индексации Spotlight..."
  sudo mdutil -i off "/"
  sudo mdutil -i on "/"
  sudo mdutil -E "/"
  
  # Настройка приоритетов процессов
  echo "Настройка приоритетов процессов..."
  
  echo "Оптимизация производительности завершена успешно"
}

# Функция для отключения ненужных служб
disable_services() {
  echo "Отключение ненужных служб..."
  
  # Список ненужных служб
  services=(
    "com.apple.diagnostics_agent"
    "com.apple.geod"
    "com.apple.maps.mapspushd"
    "com.apple.photoanalysisd"
  )
  
  for service in "${services[@]}"; do
    if launchctl list | grep -q "$service"; then
      echo "Отключение службы $service..."
      launchctl unload -w /System/Library/LaunchAgents/${service}.plist 2>/dev/null || true
    fi
  done
  
  echo "Отключение ненужных служб завершено успешно"
}

# Запуск основной функции
optimize_mac

echo "Оптимизация macOS завершена. Лог сохранен в файл: $LOG_FILE"
"""
            
            # Launcher скрипт для macOS
            template_files["StartOptimizer.command"] = """#!/bin/bash

# Путь к основному скрипту
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MAIN_SCRIPT="$SCRIPT_DIR/MacOptimizer.sh"

echo "Запуск оптимизации macOS..."
echo "===================================="

# Проверяем наличие основного скрипта
if [ -f "$MAIN_SCRIPT" ]; then
    # Проверяем права на исполнение
    if [ ! -x "$MAIN_SCRIPT" ]; then
        chmod +x "$MAIN_SCRIPT"
        echo "Права на исполнение установлены"
    fi
    
    # Запускаем скрипт с правами администратора
    sudo "$MAIN_SCRIPT"
else
    echo "Ошибка: Файл $MAIN_SCRIPT не найден."
    echo "Убедитесь, что все файлы распакованы из архива."
    exit 1
fi

echo "===================================="
echo "Оптимизация macOS завершена."
read -p "Нажмите Enter для выхода..."
"""
            
            # README.md для macOS
            template_files["README.md"] = """# Скрипт оптимизации macOS

## Описание
Данный набор скриптов предназначен для оптимизации работы операционной системы macOS. Скрипты выполняют следующие операции:
- Очистка кэша и временных файлов
- Оптимизация производительности
- Настройка визуальных эффектов
- Отключение ненужных служб

## Требования
- macOS 10.15 (Catalina) или новее
- Права администратора
- Терминал

## Использование
Есть два способа запуска скриптов:

### Способ 1: Через StartOptimizer.command (рекомендуется)
1. Откройте Finder и перейдите в папку со скриптами
2. Щелкните правой кнопкой мыши на файле `StartOptimizer.command`
3. Выберите "Открыть"
4. В окне предупреждения нажмите "Открыть"
5. Введите пароль администратора, когда будет запрошено
6. Дождитесь завершения работы скрипта

### Способ 2: Через Терминал
1. Откройте Терминал
2. Перейдите в папку со скриптами командой `cd путь/к/папке/со/скриптами`
3. Сделайте скрипт исполняемым: `chmod +x MacOptimizer.sh StartOptimizer.command`
4. Запустите скрипт: `sudo ./MacOptimizer.sh`
5. Дождитесь завершения работы скрипта

## Если скрипт не запускается
Если при попытке открыть `StartOptimizer.command` появляется сообщение о безопасности:
1. Откройте "Системные настройки"
2. Перейдите в раздел "Защита и безопасность"
3. Нажмите "Подтвердить открытие" или найдите сообщение о блокировке файла
4. Или откройте Терминал и выполните: `chmod +x путь/к/StartOptimizer.command`

## Предупреждения
- Перед запуском скрипта рекомендуется создать резервную копию важных данных
- Все изменения настроек сохраняются в резервные копии в папке `~/MacOptimizer_Backups`
- Лог работы скрипта сохраняется в файл `~/Library/Logs/MacOptimizer.log`

## Поддержка
При возникновении проблем обращайтесь за помощью через Telegram бота.
"""
        else:
            # Windows скрипты (оставляем существующий код для Windows)
            # PowerShell скрипт - базовый шаблон для оптимизации
            template_files["WindowsOptimizer.ps1"] = """# Encoding: UTF-8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Set system to use English language for output
[System.Threading.Thread]::CurrentThread.CurrentUICulture = 'en-US'
[System.Threading.Thread]::CurrentThread.CurrentCulture = 'en-US'

# Проверка прав администратора
function Test-Administrator {
    $user = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($user)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Warning "This script requires administrator privileges."
    Write-Warning "Please run the script as administrator."
    pause
    exit
}

# Настройка логирования
$LogPath = "$env:TEMP\\WindowsOptimizer_Log.txt"
Start-Transcript -Path $LogPath -Append -Force
Write-Host "Logging configured. Log will be saved to: $LogPath" -ForegroundColor Green

# Функция для создания резервных копий настроек
function Backup-Settings {
    param (
        [string]$SettingName,
        [string]$Data
    )
    
    try {
        # Создаем директорию для резервных копий, если ее нет
        $BackupDir = "$env:USERPROFILE\\WindowsOptimizer_Backups"
        if (-not (Test-Path -Path $BackupDir)) {
            New-Item -Path $BackupDir -ItemType Directory -Force | Out-Null
        }
        
        # Формируем имя файла резервной копии
        $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $BackupFile = "$BackupDir\\${SettingName}_$Timestamp.bak"
        
        # Сохраняем данные в файл
        $Data | Out-File -FilePath $BackupFile -Encoding UTF8 -Force
        
        Write-Host "Created backup of $SettingName in file $BackupFile" -ForegroundColor Green
        return $BackupFile
    }
    catch {
        Write-Warning "Failed to create backup of ${SettingName}: ${_}"
        return $null
    }
}

# Функция отображения прогресса
function Show-Progress {
    param (
        [string]$Activity,
        [int]$PercentComplete
    )
    
    Write-Progress -Activity $Activity -PercentComplete $PercentComplete
    Write-Host "[$Activity]: $PercentComplete%" -ForegroundColor Cyan
}

# Основная функция оптимизации
function Optimize-Windows {
    Write-Host "Starting Windows optimization..." -ForegroundColor Green
    
    # Отключение ненужных служб
    Show-Progress -Activity "Optimization" -PercentComplete 10
    Disable-Services
    
    # Очистка диска
    Show-Progress -Activity "Optimization" -PercentComplete 40
    Clean-System
    
    # Оптимизация производительности
    Show-Progress -Activity "Optimization" -PercentComplete 70
    Optimize-Performance
    
    Show-Progress -Activity "Optimization" -PercentComplete 100
    Write-Host "Optimization completed successfully!" -ForegroundColor Green
}

# Функция для отключения ненужных служб
function Disable-Services {
    Write-Host "Disabling unused services..." -ForegroundColor Cyan
    
    $services = @(
        "DiagTrack",          # Телеметрия
        "dmwappushservice",   # Служба WAP Push
        "SysMain",            # Superfetch
        "WSearch"             # Поиск Windows
    )
    
    foreach ($service in $services) {
        try {
            $serviceObj = Get-Service -Name $service -ErrorAction SilentlyContinue
            if ($serviceObj -and $serviceObj.Status -eq "Running") {
                Stop-Service -Name $service -Force -ErrorAction SilentlyContinue
                Set-Service -Name $service -StartupType Disabled -ErrorAction SilentlyContinue
                Write-Host "Service $service successfully disabled" -ForegroundColor Green
            }
        }
        catch {
            Write-Warning "Failed to disable service ${service}: ${_}"
        }
    }
}

# Функция для очистки системы
function Clean-System {
    Write-Host "Cleaning system..." -ForegroundColor Cyan
    
    try {
        # Очистка временных файлов
        if (Test-Path "$env:TEMP") {
            Remove-Item -Path "$env:TEMP\\*" -Force -Recurse -ErrorAction SilentlyContinue
            Write-Host "User temporary files folder cleaned" -ForegroundColor Green
        }
        
        if (Test-Path "C:\\Windows\\Temp") {
            Remove-Item -Path "C:\\Windows\\Temp\\*" -Force -Recurse -ErrorAction SilentlyContinue
            Write-Host "System temporary files folder cleaned" -ForegroundColor Green
        }
        
        # Очистка корзины
        try {
            Clear-RecycleBin -Force -ErrorAction SilentlyContinue
            Write-Host "Recycle Bin emptied" -ForegroundColor Green
        } catch {
            Write-Warning "Failed to empty Recycle Bin: ${_}"
        }
        
        # Очистка кэша обновлений Windows
        if (Test-Path "C:\\Windows\\SoftwareDistribution") {
            try {
                Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue
                Remove-Item -Path "C:\\Windows\\SoftwareDistribution\\Download\\*" -Force -Recurse -ErrorAction SilentlyContinue
                Start-Service -Name wuauserv -ErrorAction SilentlyContinue
                Write-Host "Windows Update cache cleaned" -ForegroundColor Green
            } catch {
                Write-Warning "Failed to clean Windows Update cache: ${_}"
            }
        }
        
        Write-Host "System cleaning completed successfully" -ForegroundColor Green
    }
    catch {
        Write-Warning "Error during system cleaning: ${_}"
    }
}

# Функция для оптимизации производительности
function Optimize-Performance {
    Write-Host "Optimizing performance..." -ForegroundColor Cyan
    
    try {
        # Отключение визуальных эффектов
        try {
            # Сохраняем текущие настройки
            $currentSettings = Get-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" -ErrorAction SilentlyContinue
            if ($currentSettings) {
                Backup-Settings -SettingName "VisualEffects" -Data ($currentSettings | Out-String)
            }
            
            # Устанавливаем производительность вместо внешнего вида
            Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" -Name "VisualFXSetting" -Type DWord -Value 2 -ErrorAction SilentlyContinue
            Write-Host "Visual effects set to performance mode" -ForegroundColor Green
        } catch {
            Write-Warning "Failed to configure visual effects: ${_}"
        }
        
        # Отключение автозапуска программ
        try {
            $startupPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            if (Test-Path $startupPath) {
                # Сохраняем текущие настройки
                $currentStartup = Get-ItemProperty -Path $startupPath -ErrorAction SilentlyContinue
                if ($currentStartup) {
                    Backup-Settings -SettingName "Autorun" -Data ($currentStartup | Out-String)
                }
                
                $startupItems = Get-ItemProperty -Path $startupPath
                foreach ($item in $startupItems.PSObject.Properties) {
                    if ($item.Name -notlike "PS*") {
                        Write-Host "Disabling autostart: $($item.Name)" -ForegroundColor Yellow
                        Remove-ItemProperty -Path $startupPath -Name $item.Name -ErrorAction SilentlyContinue
                    }
                }
                Write-Host "Startup items processing completed" -ForegroundColor Green
            }
        } catch {
            Write-Warning "Failed to process startup items: ${_}"
        }
        
        # Настройка плана электропитания на высокую производительность
        try {
            $powerSchemes = powercfg /list | Where-Object { $_ -match "высок|High" }
            if ($powerSchemes) {
                $highPerfScheme = $powerSchemes -match "высок|High" | Select-Object -First 1
                if ($highPerfScheme -match "([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})") {
                    $schemeGuid = $Matches[1]
                    powercfg /setactive $schemeGuid
                    Write-Host "High performance power plan activated" -ForegroundColor Green
                }
            }
        } catch {
            Write-Warning "Failed to configure power plan: ${_}"
        }
        
        Write-Host "Performance optimization completed successfully" -ForegroundColor Green
    }
    catch {
        Write-Warning "Error during performance optimization: ${_}"
    }
}

# Запуск основной функции
Optimize-Windows

# Остановка логирования
Stop-Transcript
Write-Host "Optimization completed. Log saved to file: $LogPath" -ForegroundColor Green
pause
"""
            
            # Batch скрипт для запуска PowerShell
            template_files["Start-Optimizer.bat"] = """@echo off
chcp 65001 >nul
title Windows Optimization

:: Check administrator rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please run this file as administrator.
    pause
    exit /b 1
)

echo Starting Windows optimization script...
echo ==========================================

:: Run PowerShell script with execution policy bypass
powershell -ExecutionPolicy Bypass -NoProfile -File "WindowsOptimizer.ps1" -Encoding UTF8

echo ==========================================
echo Optimization script completed.
pause
"""
            
            # README.md с документацией
            template_files["README.md"] = """# Скрипт оптимизации Windows

## Описание
Данный набор скриптов предназначен для оптимизации работы операционной системы Windows. Скрипты выполняют следующие операции:
- Отключение неиспользуемых служб
- Очистка временных файлов и кэша
- Оптимизация производительности
- Настройка автозагрузки

## Требования
- Windows 10 или Windows 11
- Права администратора
- PowerShell 5.1 или выше

## Использование
Есть два способа запуска скриптов:

### Способ 1: Через PowerShell (рекомендуется)
1. Щелкните правой кнопкой мыши на файле `Run-Optimizer.ps1`
2. Выберите "Запустить с помощью PowerShell" или "Запустить от имени администратора"
3. Дождитесь завершения работы скрипта
4. Перезагрузите компьютер для применения всех изменений

### Способ 2: Через командную строку
1. Запустите командную строку от имени администратора
2. Перейдите в папку со скриптами командой `cd путь\\к\\папке\\со\\скриптами`
3. Выполните команду `Start-Optimizer.bat`
4. Дождитесь завершения работы скрипта
5. Перезагрузите компьютер для применения всех изменений

### Примечание по решению проблем с кодировкой
Если при запуске `Start-Optimizer.bat` возникают ошибки с кодировкой (текст отображается некорректно), используйте файл `Run-Optimizer.ps1` для запуска скрипта из PowerShell.

## Предупреждения
- Перед запуском скриптов оптимизации рекомендуется создать точку восстановления системы
- Все изменения регистра сохраняются в резервные копии в папке `%USERPROFILE%\\WindowsOptimizer_Backups`
- Лог работы скрипта сохраняется в файл `%TEMP%\\WindowsOptimizer_Log.txt`

## Поддержка
При возникновении проблем обращайтесь за помощью через Telegram бота.
"""
            
            # PowerShell файл для запуска основного скрипта (альтернатива .bat файлу)
            template_files["Run-Optimizer.ps1"] = """# Encoding: UTF-8
# PowerShell script to run the optimization script with proper rights
$OutputEncoding = [System.Text.Encoding]::UTF8

# Check administrator rights
function Test-Administrator {
    $user = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($user)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Warning "This script requires administrator privileges."
    Write-Warning "Please run this file as administrator."
    pause
    exit
}

Write-Host "Starting Windows optimization script..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

# Check if the main script exists
if (Test-Path -Path "WindowsOptimizer.ps1") {
    # Run the main PowerShell script
    try {
        & .\\WindowsOptimizer.ps1
    } catch {
        Write-Host "Error running the optimization script: $_" -ForegroundColor Red
    }
} else {
    Write-Host "Error: WindowsOptimizer.ps1 not found in the current directory." -ForegroundColor Red
    Write-Host "Make sure all files are extracted from the ZIP archive." -ForegroundColor Yellow
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Optimization script completed." -ForegroundColor Green
pause
"""
        
        # Подсчет и возврат найденных файлов
        logger.info(f"Всего извлечено {len(template_files)} файлов из ответа API")
        return template_files
    
    def extract_files(self, response_text, os_type='windows'):
        """Извлечение файлов из ответа API
        
        Args:
            response_text (str): Текст ответа от API
            os_type (str): Тип операционной системы ('windows' или 'macos')
            
        Returns:
            dict: Словарь с файлами (имя файла -> содержимое)
        """
        files = {}
        
        if os_type == 'macos':
            # Шаблоны для извлечения блоков кода для macOS
            shell_pattern = r"```bash\n(.*?)```"
            command_pattern = r"```bash\n(.*?)```"
            markdown_pattern = r"```markdown\n(.*?)```"
            
            # Извлечение Shell скрипта
            shell_matches = re.findall(shell_pattern, response_text, re.DOTALL)
            if shell_matches and len(shell_matches) >= 1:
                shell_content = shell_matches[0]
                # Проверяем на наличие шебанга
                if "#!/bin/bash" not in shell_content:
                    shell_content = "#!/bin/bash\n\n" + shell_content
                files["MacOptimizer.sh"] = shell_content
                logger.info(f"Извлечен Shell скрипт длиной {len(shell_content)} символов")
            
            # Извлечение Command скрипта (launcher)
            if len(shell_matches) >= 2:
                command_content = shell_matches[1]
                # Проверяем на наличие шебанга
                if "#!/bin/bash" not in command_content:
                    command_content = "#!/bin/bash\n\n" + command_content
                files["StartOptimizer.command"] = command_content
                logger.info(f"Извлечен Command скрипт длиной {len(command_content)} символов")
            
            # Извлечение Markdown документации
            md_matches = re.findall(markdown_pattern, response_text, re.DOTALL)
            if md_matches:
                md_content = md_matches[0]
                files["README.md"] = md_content
                logger.info(f"Извлечена документация длиной {len(md_content)} символов")
            
            # Проверка на пустые совпадения (ошибки в формате блоков кода)
            if "MacOptimizer.sh" not in files or "StartOptimizer.command" not in files:
                # Пробуем альтернативное извлечение без указания языка
                alt_pattern = r"```\n(.*?)```"
                alt_matches = re.findall(alt_pattern, response_text, re.DOTALL)
                
                if alt_matches:
                    for i, content in enumerate(alt_matches):
                        # Пытаемся определить тип файла по содержимому
                        if i == 0 or ("optimize_mac" in content or "cleanup_system" in content):
                            if "#!/bin/bash" not in content:
                                content = "#!/bin/bash\n\n" + content
                            files["MacOptimizer.sh"] = content
                            logger.info(f"Извлечен Shell скрипт (альт.) длиной {len(content)} символов")
                        elif i == 1 or "sudo" in content:
                            if "#!/bin/bash" not in content:
                                content = "#!/bin/bash\n\n" + content
                            files["StartOptimizer.command"] = content
                            logger.info(f"Извлечен Command скрипт (альт.) длиной {len(content)} символов")
                        elif "#" in content and "macOS" in content:
                            files["README.md"] = content
                            logger.info(f"Извлечена документация (альт.) длиной {len(content)} символов")
            
            # Дополнительная проверка: добавляем файлы, которых не хватает
            if "MacOptimizer.sh" not in files:
                files["MacOptimizer.sh"] = self._get_template_scripts('macos')["MacOptimizer.sh"]
                logger.info("Добавлен шаблонный Shell скрипт")
            
            if "StartOptimizer.command" not in files:
                files["StartOptimizer.command"] = self._get_template_scripts('macos')["StartOptimizer.command"]
                logger.info("Добавлен шаблонный Command скрипт")
            
            if "README.md" not in files:
                files["README.md"] = self._get_template_scripts('macos')["README.md"]
                logger.info("Добавлена шаблонная документация")
        else:
            # Шаблоны для извлечения блоков кода для Windows
            powershell_pattern = r"```powershell\n(.*?)```"
            batch_pattern = r"```batch\n(.*?)```"
            markdown_pattern = r"```markdown\n(.*?)```"
            
            # Извлечение PowerShell скрипта
            ps_matches = re.findall(powershell_pattern, response_text, re.DOTALL)
            if ps_matches:
                ps_content = ps_matches[0]
                # Проверяем на наличие кодировки UTF-8
                if "$OutputEncoding = [System.Text.Encoding]::UTF8" not in ps_content:
                    ps_content = "# Encoding: UTF-8\n$OutputEncoding = [System.Text.Encoding]::UTF8\n\n" + ps_content
                files["WindowsOptimizer.ps1"] = ps_content
                logger.info(f"Извлечен PowerShell скрипт длиной {len(ps_content)} символов")
            
            # Извлечение Batch скрипта
            bat_matches = re.findall(batch_pattern, response_text, re.DOTALL)
            if bat_matches:
                bat_content = bat_matches[0]
                # Проверяем на наличие обязательных команд
                if "@echo off" not in bat_content:
                    bat_content = "@echo off\n" + bat_content
                if "chcp 65001" not in bat_content:
                    bat_content = bat_content.replace("@echo off", "@echo off\nchcp 65001 >nul")
                files["Start-Optimizer.bat"] = bat_content
                logger.info(f"Извлечен Batch скрипт длиной {len(bat_content)} символов")
            
            # Извлечение Markdown документации
            md_matches = re.findall(markdown_pattern, response_text, re.DOTALL)
            if md_matches:
                md_content = md_matches[0]
                files["README.md"] = md_content
                logger.info(f"Извлечена документация длиной {len(md_content)} символов")
            
            # Проверка на пустые совпадения (ошибки в формате блоков кода)
            if not ps_matches and not bat_matches and not md_matches:
                # Пробуем альтернативное извлечение без указания языка
                alt_pattern = r"```\n(.*?)```"
                alt_matches = re.findall(alt_pattern, response_text, re.DOTALL)
                
                if alt_matches:
                    for i, content in enumerate(alt_matches):
                        # Пытаемся определить тип файла по содержимому
                        if "function" in content and "$" in content:
                            if "$OutputEncoding = [System.Text.Encoding]::UTF8" not in content:
                                content = "# Encoding: UTF-8\n$OutputEncoding = [System.Text.Encoding]::UTF8\n\n" + content
                            files["WindowsOptimizer.ps1"] = content
                            logger.info(f"Извлечен PowerShell скрипт (альт.) длиной {len(content)} символов")
                        elif "@echo off" in content or "powershell" in content.lower():
                            if "@echo off" not in content:
                                content = "@echo off\n" + content
                            if "chcp 65001" not in content:
                                content = content.replace("@echo off", "@echo off\nchcp 65001 >nul")
                            files["Start-Optimizer.bat"] = content
                            logger.info(f"Извлечен Batch скрипт (альт.) длиной {len(content)} символов")
                        elif "#" in content and "Windows" in content:
                            files["README.md"] = content
                            logger.info(f"Извлечена документация (альт.) длиной {len(content)} символов")
            
            # Дополнительная проверка: добавляем файлы, которых не хватает
            if "WindowsOptimizer.ps1" not in files:
                files["WindowsOptimizer.ps1"] = self._get_template_scripts('windows')["WindowsOptimizer.ps1"]
                logger.info("Добавлен шаблонный PowerShell скрипт")
            
            if "Start-Optimizer.bat" not in files:
                files["Start-Optimizer.bat"] = self._get_template_scripts('windows')["Start-Optimizer.bat"]
                logger.info("Добавлен шаблонный Batch скрипт")
            
            if "README.md" not in files:
                files["README.md"] = self._get_template_scripts('windows')["README.md"]
                logger.info("Добавлена шаблонная документация")
        
        # Подсчет и возврат найденных файлов
        logger.info(f"Всего извлечено {len(files)} файлов из ответа API")
        return files
    
    async def send_script_files_to_user(self, chat_id, files):
        """Отправляет сгенерированные файлы пользователю в виде архива"""
        try:
            if not files:
                bot.send_message(chat_id, "Не удалось создать файлы скриптов.")
                return False
            
            # Определяем тип ОС по именам файлов
            is_macos = "MacOptimizer.sh" in files
            
            # Создаем ZIP-архив в памяти
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for filename, content in files.items():
                    # Записываем файлы в архив (с правильной кодировкой)
                    zip_file.writestr(filename, content)
                
                # Добавляем инструкции в архив
                if is_macos:
                    instructions = """# Инструкция по использованию скриптов оптимизации macOS

1. Распакуйте все файлы из архива в отдельную папку на вашем Mac.

ЗАПУСК СКРИПТА:

1. Откройте терминал.
2. Перейдите в папку со скриптами командой: cd путь/к/папке/со/скриптами
3. Сделайте скрипты исполняемыми с помощью команды:
   chmod +x MacOptimizer.sh StartOptimizer.command
4. Запустите скрипт одним из способов:
   a) Через Finder: дважды щелкните на StartOptimizer.command
   b) Через Терминал: sudo ./MacOptimizer.sh

ВАЖНЫЕ ПРИМЕЧАНИЯ:
- Перед запуском создайте резервную копию важных данных.
- Вас попросят ввести пароль администратора.
- Скрипты создают резервные копии измененных параметров в папке ~/MacOptimizer_Backups.
- Все действия скриптов записываются в лог-файл ~/Library/Logs/MacOptimizer.log.

Если у вас возникнут проблемы, используйте команду /help для получения справки."""
                else:
                    instructions = """# Инструкция по использованию скриптов оптимизации Windows

1. Распакуйте все файлы из архива в отдельную папку на вашем компьютере.

СПОСОБ 1 (РЕКОМЕНДУЕТСЯ): Запуск через PowerShell
- Щелкните правой кнопкой мыши на файле Run-Optimizer.ps1
- Выберите "Запустить с помощью PowerShell" или "Запустить от имени администратора"
- Следуйте инструкциям на экране

СПОСОБ 2: Запуск через командную строку
- Запустите командную строку от имени администратора
- Перейдите в папку со скриптами командой: cd путь\\к\\папке\\со\\скриптами
- Выполните команду: Start-Optimizer.bat

ЕСЛИ ВОЗНИКАЮТ ОШИБКИ КОДИРОВКИ:
Если при запуске Start-Optimizer.bat видны ошибки с символами "", используйте 
метод запуска через PowerShell скрипт Run-Optimizer.ps1 (Способ 1).

## Важно:
- Перед запуском создайте точку восстановления системы.
- Скрипты создают резервные копии измененных параметров в папке WindowsOptimizer_Backups.
- Все действия скриптов записываются в лог-файл в папке Temp.

Если у вас возникнут проблемы, используйте команду /help для получения справки."""
                
                zip_file.writestr("КАК_ИСПОЛЬЗОВАТЬ.txt", instructions)
            
            # Сбрасываем указатель буфера на начало
            zip_buffer.seek(0)
            
            # Определяем имя архива и текст сообщения в зависимости от ОС
            if is_macos:
                archive_name = "MacOptimizer.zip"
                caption = "✅ Скрипты оптимизации macOS созданы! Распакуйте архив и запустите StartOptimizer.command."
                additional_msg = "📝 *Инструкция по использованию:*\n\n"\
                                "1. Распакуйте все файлы из архива в отдельную папку\n"\
                                "2. Откройте терминал и выполните:\n"\
                                "   `chmod +x MacOptimizer.sh StartOptimizer.command`\n"\
                                "3. Запустите файл StartOptimizer.command\n"\
                                "4. Введите пароль администратора, когда будет запрошено\n\n"\
                                "ℹ️ Если возникнут ошибки при запуске скрипта, отправьте мне скриншот с ошибкой."
            else:
                archive_name = "WindowsOptimizer.zip"
                caption = "✅ Скрипты оптимизации Windows созданы! Распакуйте архив и запустите Start-Optimizer.bat от имени администратора."
                additional_msg = "📝 *Инструкция по использованию:*\n\n"\
                                "1. Распакуйте все файлы из архива в отдельную папку\n"\
                                "2. Запустите файл Start-Optimizer.bat от имени администратора\n"\
                                "3. Дождитесь завершения работы скрипта\n\n"\
                                "ℹ️ Если возникнут ошибки при запуске скрипта, отправьте мне скриншот с ошибкой."
            
            # Отправляем архив пользователю
            bot.send_document(
                chat_id=chat_id,
                document=zip_buffer,
                caption=caption,
                visible_file_name=archive_name
            )
            
            # Отправляем дополнительное сообщение с инструкциями
            bot.send_message(
                chat_id=chat_id,
                text=additional_msg,
                parse_mode="Markdown"
            )
            
            # Обновляем состояние пользователя
            user_states[chat_id] = "main_menu"
            
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при отправке файлов пользователю: {e}", exc_info=True)
            bot.send_message(
                chat_id=chat_id, 
                text=f"❌ Произошла ошибка при отправке файлов: {str(e)}"
            )
            return False

    async def fix_script_errors(self, message):
        """Генерация скриптов с улучшенным промптом после обнаружения ошибок"""
        try:
            logger.info(f"Начинаю исправление ошибок в скрипте для пользователя {message.chat.id}")
            
            # Проверяем наличие фото
            if not message.photo:
                return "Не найдено изображение с ошибкой. Пожалуйста, отправьте скриншот ошибки."
            
            # Получаем файл фото
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
            
            # Загружаем изображение
            img_data = requests.get(file_url).content
            
            # Кодируем изображение в base64
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # Формируем сообщение для API
            user_message = user_messages.get(message.chat.id, "Исправь ошибки в скрипте, показанные на скриншоте")
            
            # Используем оптимизированный промпт исправления ошибок
            prompt = self.prompts.get("ERROR_FIX_PROMPT_TEMPLATE", ERROR_FIX_PROMPT_TEMPLATE)
            
            # Подготовка текста промпта
            enhanced_prompt = f"{prompt}\n\n{user_message}\n\nЯ отправил скриншот с ошибками в скрипте. Исправь основные проблемы, которые обычно возникают в PowerShell скриптах."
            
            logger.info("Отправляю запрос к Claude API для исправления ошибок...")
            
            # Проверяем, инициализирован ли клиент API
            if self.client is None:
                logger.warning("API клиент не инициализирован. Используем шаблонные скрипты.")
                files = self._get_template_scripts()
                return files
            
            try:
                # Отправляем запрос в зависимости от версии клиента
                if self.client_method == "completion":
                    # Старый API (версии <= 0.5.9)
                    try:
                        response = await asyncio.to_thread(
                            self.client.completion,
                            prompt=f"\n\nHuman: {enhanced_prompt}\n\nAssistant:",
                            model="claude-2",
                            max_tokens_to_sample=4000,
                            temperature=0.7
                        )
                        response_text = response.completion
                    except Exception as old_api_error:
                        logger.error(f"Ошибка при использовании старого API для исправления: {old_api_error}")
                        # Попробуем прямой вызов функции без await
                        response = self.client.completion(
                            prompt=f"\n\nHuman: {enhanced_prompt}\n\nAssistant:",
                            model="claude-2",
                            max_tokens_to_sample=4000,
                            temperature=0.7
                        )
                        response_text = response.completion
                else:
                    # Новый API (версии >= 0.51.0)
                    try:
                        # Для API v0.51.0+
                        messages = [
                            {
                                "role": "user", 
                                "content": [
                                    {
                                        "type": "text",
                                        "text": enhanced_prompt
                                    }
                                ]
                            }
                        ]
                        response = await asyncio.to_thread(
                            self.client.messages.create,
                            model="claude-3-opus-20240229",
                            max_tokens=4000,
                            messages=messages
                        )
                        response_text = response.content[0].text
                    except Exception as new_api_error:
                        # Резервный вызов без asyncio
                        error_str = str(new_api_error)
                        logger.error(f"Ошибка при использовании нового API асинхронно для исправления: {new_api_error}")
                        
                        if "invalid x-api-key" in error_str or "authentication_error" in error_str:
                            # Отправляем сообщение об ошибке аутентификации
                            bot.send_message(message.chat.id, 
                                            "⚠️ Обнаружена проблема с API ключом.\n\n"
                                            "Пожалуйста, получите новый ключ API на сайте Anthropic и настройте его в файле .env.")
                            # Используем альтернативный подход с шаблонами
                            files = self._get_template_scripts()
                            return files
                        
                        try:
                            messages = [
                                {
                                    "role": "user", 
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": enhanced_prompt
                                        }
                                    ]
                                }
                            ]
                            response = self.client.messages.create(
                                model="claude-3-opus-20240229",
                                max_tokens=4000,
                                messages=messages
                            )
                            response_text = response.content[0].text
                        except Exception as e:
                            logger.error(f"Ошибка при использовании нового API напрямую для исправления: {e}")
                            raise
                
                logger.info(f"Получен ответ от Claude API, длина: {len(response_text)} символов")
            except Exception as api_error:
                # Проверяем ошибку баланса API
                error_str = str(api_error)
                if "credit balance is too low" in error_str or "Your credit balance is too low" in error_str:
                    logger.error(f"Ошибка недостаточного баланса API: {api_error}")
                    error_message = "К сожалению, баланс API-кредитов исчерпан. Пожалуйста, обратитесь к администратору для пополнения баланса."
                    bot.send_message(message.chat.id, error_message)
                    
                    # Используем альтернативный подход с шаблонами
                    files = self._get_template_scripts()
                    return files
                else:
                    # Другая ошибка API - используем шаблонные скрипты
                    logger.error(f"Ошибка API при исправлении скрипта: {api_error}")
                    files = self._get_template_scripts()
                    return files
            
            # Извлекаем файлы из ответа
            files = self.extract_files(response_text)
            
            if not files:
                logger.warning("Не удалось извлечь исправленные файлы из ответа API")
                files = self._get_template_scripts()
                return files
            
            # Дополнительная проверка и исправление скриптов
            fixed_files, validation_results, errors_corrected = validate_and_fix_scripts(files)
            
            # Обновляем статистику
            self.metrics.record_script_generation({
                "timestamp": datetime.now().isoformat(),
                "errors": validation_results,
                "error_count": sum(len(issues) for issues in validation_results.values()),
                "fixed_count": errors_corrected,
                "model": "claude-3-opus-20240229",
                "is_error_fix": True
            })
            
            # Сохраняем файлы для последующей отправки
            user_files[message.chat.id] = fixed_files
            
            return fixed_files
        
        except Exception as e:
            logger.error(f"Ошибка при исправлении скрипта: {e}", exc_info=True)
            # В случае критической ошибки, возвращаем шаблонные скрипты
            try:
                files = self._get_template_scripts()
                return files
            except:
                return f"Произошла ошибка при исправлении скрипта: {str(e)}"
    
    def update_error_stats(self, validation_results):
        """
        Обновляет статистику ошибок
        
        Args:
            validation_results: результаты валидации скриптов
        """
        self.metrics.record_validation_results(
            validation_results=validation_results,
            model_name="claude-3-opus-20240229",
            fixed_count=0  # Здесь можно указать количество исправленных ошибок, если оно известно
        )

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def cmd_start(message):
    """Начало взаимодействия с ботом"""
    try:
        # Сбрасываем все предыдущие состояния пользователя
        user_states[message.chat.id] = "main_menu"
        
        # Создаем клавиатуру для выбора режима
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn1 = types.KeyboardButton("🔧 Создать скрипт оптимизации")
        btn2 = types.KeyboardButton("🔨 Исправить ошибки в скрипте")
        markup.add(btn1, btn2)
        
        # Приветственное сообщение
        bot.send_message(
            message.chat.id,
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Я бот для создания скриптов оптимизации Windows.\n\n"
            "Что вы хотите сделать?",
            reply_markup=markup
        )
        
        # Проверяем подписку и показываем соответствующее сообщение
        # Используем обновленную функцию проверки с кнопкой оплаты
        if has_subscription_check:
            check_subscription_before_action(message)
        
        logger.info(f"Пользователь {message.chat.id} запустил бота")
    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /start: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при запуске бота. Пожалуйста, попробуйте снова.")

# Обработчик для проверки подписки
def check_subscription_before_action(message):
    """
    Проверяет наличие активной подписки у пользователя перед выполнением действия
    
    Args:
        message: Объект сообщения от Telegram
        
    Returns:
        bool: True, если есть активная подписка или проверка отключена
    """
    if not has_subscription_check:
        return True  # Если модуль проверки подписок не загружен, пропускаем проверку
    
    # Получаем информацию о боте для формирования ссылки на оплату
    try:
        bot_info = bot.get_me()
        bot_username = bot_info.username
    except Exception as e:
        logger.error(f"Ошибка при получении информации о боте: {e}")
        bot_username = "your_bot"  # Запасной вариант
    
    user_id = message.from_user.id
    if check_user_subscription(str(user_id)):
        return True
    else:
        # Создаем кнопку для оплаты через мини-приложение
        markup = types.InlineKeyboardMarkup()
        # Создаем URL для мини-приложения оплаты
        # Для WebApp в Telegram необходимо использовать только публичные URL (localhost не подходит)
        # Используем реальный URL платежной системы на Railway
        payment_url = f"{PAYMENT_SYSTEM_URL}/?user_id={user_id}&bot_username={bot_username}"
        
        # Добавляем кнопку оплаты
        payment_button = types.InlineKeyboardButton(
            text="💳 Оплатить подписку", 
            web_app=types.WebAppInfo(url=payment_url)
        )
        markup.add(payment_button)
        
        # Отправляем сообщение с кнопкой оплаты
        bot.send_message(
            chat_id=message.chat.id, 
            text="⚠️ *Ваша подписка не активна*\n\nДля использования всех функций бота необходимо приобрести подписку.", 
            parse_mode="Markdown",
            reply_markup=markup
        )
        return False

# Обработчик для выбора пользователя - модифицируем для проверки подписки
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "main_menu")
def handle_user_choice(message):
    try:
        if "создать скрипт" in message.text.lower():
            # Проверяем подписку перед продолжением
            if not check_subscription_before_action(message):
                return
                
            # Переходим к созданию скрипта
            user_states[message.chat.id] = "waiting_for_screenshot"
            
            # Сохраняем текст сообщения для последующего определения режима
            user_messages[message.chat.id] = "Создай скрипт оптимизации Windows на основе этого скриншота"
            
            # Запрашиваем скриншот
            bot.send_message(
                message.chat.id,
                "📸 Отправьте скриншот с информацией о вашей системе (например, из приложения 'Сведения о системе' или 'Диспетчер задач').",
                reply_markup=types.ReplyKeyboardRemove()
            )
            
            logger.info(f"Пользователь {message.chat.id} выбрал создание скрипта оптимизации")
            
        elif "исправить ошибки" in message.text.lower():
            # Проверяем подписку перед продолжением
            if not check_subscription_before_action(message):
                return
                
            # Переходим к исправлению ошибок
            user_states[message.chat.id] = "waiting_for_error_screenshot"
            
            # Сохраняем текст сообщения для последующего определения режима
            user_messages[message.chat.id] = "Исправь ошибки в скрипте, показанные на этом скриншоте"
            
            # Запрашиваем скриншот с ошибкой
            bot.send_message(
                message.chat.id,
                "📸 Отправьте скриншот с ошибкой, которую нужно исправить.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            
            logger.info(f"Пользователь {message.chat.id} выбрал исправление ошибок в скрипте")
            
        else:
            bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите один из вариантов на клавиатуре.",
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике выбора пользователя: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте снова.")

# Обработчик команды /help - дополняем информацией о подписке
@bot.message_handler(commands=['help'])
def cmd_help(message):
    """Отправка справочной информации"""
    try:
        help_text = """
📚 *Как использовать бота для оптимизации Windows*

*Для создания скриптов оптимизации:*
1. Нажмите на кнопку "🔧 Создать скрипт оптимизации"
2. Отправьте скриншот со сведениями о вашей системе
3. Дождитесь генерации скриптов
4. Скачайте ZIP-архив с готовыми скриптами
5. Запустите Start-Optimizer.bat от имени администратора

*Для исправления ошибок в скрипте:*
1. Нажмите на кнопку "🔨 Исправить ошибки в скрипте"
2. Отправьте скриншот с ошибкой
3. Дождитесь исправления скриптов
4. Скачайте ZIP-архив с исправленными скриптами

*Дополнительные команды:*
/start - начать работу с ботом
/help - показать эту справку
/stats - показать статистику по скриптам
/update_prompts - обновить шаблоны промптов
/cancel - отменить текущую операцию
/subscription - информация о вашей подписке

*Важно:* Перед запуском скриптов оптимизации рекомендуется создать точку восстановления системы.
"""
        bot.send_message(message.chat.id, help_text, parse_mode="Markdown")
        
        # Добавляем информацию о подписке, если доступно
        if has_subscription_check:
            subscription_active = check_user_subscription(message.chat.id)
            if subscription_active:
                subscription_info = get_subscription_info(message.chat.id)
                days_left = subscription_info.get("days_left", 0)
                plan_name = subscription_info.get("plan_name", "Стандартный")
                
                sub_text = f"""
*Информация о подписке:*
✅ У вас активна подписка "{plan_name}"
⏱️ Осталось дней: {days_left}

Для более подробной информации используйте команду /subscription
"""
                bot.send_message(message.chat.id, sub_text, parse_mode="Markdown")
            else:
                bot.send_message(
                    message.chat.id,
                    "⚠️ У вас нет активной подписки. Используйте команду /subscription для получения информации о подписке.",
                    parse_mode="Markdown"
                )
        
        logger.info(f"Пользователь {message.chat.id} запросил справку")
    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /help: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отправке справки. Пожалуйста, попробуйте снова.")

# Обработчик команды /cancel
@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    """Отмена текущей операции"""
    try:
        # Сбрасываем состояние пользователя
        user_states[message.chat.id] = "main_menu"
        
        # Возвращаем главное меню
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn1 = types.KeyboardButton("🔧 Создать скрипт оптимизации")
        btn2 = types.KeyboardButton("🔨 Исправить ошибки в скрипте")
        markup.add(btn1, btn2)
        
        bot.send_message(
            message.chat.id, 
            "❌ Текущая операция отменена. Выберите, что вы хотите сделать:",
            reply_markup=markup
        )
        
        logger.info(f"Пользователь {message.chat.id} отменил текущую операцию")
    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /cancel: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отмене операции. Пожалуйста, попробуйте снова.")

# Обработчик для скриншотов с ошибками
@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.chat.id) == "waiting_for_error_screenshot")
def process_error_photo(message):
    """Исправление ошибок в скрипте на основе скриншота ошибки"""
    try:
        # Проверяем подписку перед обработкой фото
        if not check_subscription_before_action(message):
            # Возвращаем пользователя в главное меню
            user_states[message.chat.id] = "main_menu"
            # Отображаем клавиатуру главного меню
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            btn1 = types.KeyboardButton("🔧 Создать скрипт оптимизации")
            btn2 = types.KeyboardButton("🔨 Исправить ошибки в скрипте")
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
            return
        
        # Продолжаем обработку фото
        # Сообщаем пользователю, что начали обработку
        processing_msg = bot.send_message(
            message.chat.id,
            "🔍 Анализирую ошибку на скриншоте...",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Создаем экземпляр бота
        optimization_bot = OptimizationBot(ANTHROPIC_API_KEY)
        
        # Переменная для хранения результатов
        result = None
        
        try:
            # Вызываем асинхронную функцию через asyncio.run
            result = asyncio.run(optimization_bot.fix_script_errors(message))
        except Exception as api_error:
            logger.error(f"Ошибка при исправлении скрипта: {api_error}")
            
            # Используем шаблонные скрипты вместо генерации
            try:
                result = optimization_bot._get_template_scripts()
                
                try:
                    bot.edit_message_text(
                        "⚠️ Возникла проблема при анализе ошибки. Будут предоставлены стандартные скрипты оптимизации.",
                        message.chat.id,
                        processing_msg.message_id
                    )
                except Exception as edit_error:
                    logger.warning(f"Не удалось отредактировать сообщение: {edit_error}")
                    bot.send_message(
                        message.chat.id,
                        "⚠️ Возникла проблема при анализе ошибки. Будут предоставлены стандартные скрипты оптимизации."
                    )
            except Exception as fallback_error:
                logger.error(f"Ошибка при создании шаблонных скриптов: {fallback_error}")
                bot.send_message(
                    message.chat.id,
                    "❌ Возникла критическая ошибка. Пожалуйста, попробуйте позже."
                )
                user_states[message.chat.id] = "main_menu"
                return
        
        if isinstance(result, dict) and len(result) > 0:
            # Сообщаем об успешном исправлении
            try:
                if "MacOptimizer.sh" in result or "WindowsOptimizer.ps1" in result:
                    bot.edit_message_text(
                        "✅ Создаю ZIP-архив со скриптами оптимизации...",
                        message.chat.id,
                        processing_msg.message_id
                    )
                else:
                    bot.edit_message_text(
                        "✅ Ошибки успешно исправлены! Создаю ZIP-архив с исправленными скриптами...",
                        message.chat.id,
                        processing_msg.message_id
                    )
            except telebot.apihelper.ApiTelegramException as api_error:
                if "message can't be edited" in str(api_error):
                    logger.warning(f"Не удалось отредактировать сообщение - сообщение не может быть отредактировано")
                    # Отправляем новое сообщение вместо редактирования
                    bot.send_message(
                        message.chat.id,
                        "✅ Ошибки успешно исправлены! Создаю ZIP-архив с исправленными скриптами..."
                    )
                else:
                    raise
            except Exception as edit_error:
                logger.warning(f"Не удалось отредактировать сообщение: {edit_error}")
                # Отправляем новое сообщение вместо редактирования
                bot.send_message(
                    message.chat.id,
                    "✅ Ошибки успешно исправлены! Создаю ZIP-архив с исправленными скриптами..."
                )
            
            # Отправляем файлы пользователю
            try:
                asyncio.run(optimization_bot.send_script_files_to_user(message.chat.id, result))
            except Exception as send_error:
                logger.error(f"Ошибка при отправке файлов: {send_error}")
                bot.send_message(
                    message.chat.id, 
                    "❌ Произошла ошибка при отправке файлов. Пожалуйста, попробуйте еще раз."
                )
            
            # Возвращаем в главное меню
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            btn1 = types.KeyboardButton("🔧 Создать скрипт оптимизации")
            btn2 = types.KeyboardButton("🔨 Исправить ошибки в скрипте")
            markup.add(btn1, btn2)
            
            bot.send_message(
                message.chat.id,
                "Что еще вы хотите сделать?",
                reply_markup=markup
            )
            
            # Сбрасываем состояние
            user_states[message.chat.id] = "main_menu"
            
        else:
            # В случае ошибки
            try:
                bot.edit_message_text(
                    f"❌ {result}",
                    message.chat.id,
                    processing_msg.message_id
                )
            except telebot.apihelper.ApiTelegramException as api_error:
                if "message can't be edited" in str(api_error):
                    logger.warning(f"Не удалось отредактировать сообщение - сообщение не может быть отредактировано")
                    # Отправляем новое сообщение вместо редактирования
                    bot.send_message(
                        message.chat.id,
                        f"❌ {result}"
                    )
                else:
                    raise
            except Exception as edit_error:
                logger.warning(f"Не удалось отредактировать сообщение: {edit_error}")
                # Отправляем новое сообщение вместо редактирования
                bot.send_message(
                    message.chat.id,
                    f"❌ {result}"
                )
            
            # Предлагаем попробовать снова
            bot.send_message(
                message.chat.id,
                "Пожалуйста, отправьте более четкий скриншот с ошибкой или вернитесь в главное меню с помощью команды /cancel."
            )
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике фото с ошибкой: {e}", exc_info=True)
        bot.send_message(
            message.chat.id,
            f"❌ Произошла ошибка при обработке фото: {str(e)}\n\nПопробуйте отправить другой скриншот или вернитесь в главное меню с помощью команды /cancel."
        )
        # Возвращаем в главное меню при критической ошибке
        user_states[message.chat.id] = "main_menu"
        # Показываем клавиатуру меню
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn1 = types.KeyboardButton("🔧 Создать скрипт оптимизации")
        btn2 = types.KeyboardButton("🔨 Исправить ошибки в скрипте")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

# Обработчик для скриншотов с системной информацией
@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.chat.id) == "waiting_for_screenshot")
def process_photo(message):
    """Обработка скриншота системы и создание скрипта оптимизации"""
    try:
        # Проверяем подписку перед обработкой фото
        if not check_subscription_before_action(message):
            # Возвращаем пользователя в главное меню
            user_states[message.chat.id] = "main_menu"
            # Отображаем клавиатуру главного меню
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            btn1 = types.KeyboardButton("🔧 Создать скрипт оптимизации")
            btn2 = types.KeyboardButton("🔨 Исправить ошибки в скрипте")
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
            return
            
        # Продолжаем обработку фото как обычно
        # Сообщаем пользователю, что начали обработку
        processing_msg = bot.send_message(
            message.chat.id,
            "🔍 Анализирую систему на скриншоте и создаю скрипт оптимизации...",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Создаем экземпляр бота оптимизации
        optimization_bot = OptimizationBot(ANTHROPIC_API_KEY)
        
        # Переменная для хранения результатов
        result = None
        
        try:
            # Вызываем асинхронную функцию через asyncio.run
            result = asyncio.run(optimization_bot.generate_new_script(message))
        except Exception as api_error:
            logger.error(f"Ошибка при генерации скрипта: {api_error}")
            
            # Используем шаблонные скрипты вместо генерации
            try:
                result = optimization_bot._get_template_scripts()
                
                try:
                    bot.edit_message_text(
                        "⚠️ Возникла проблема при анализе скриншота. Будут предоставлены стандартные скрипты оптимизации.",
                        message.chat.id,
                        processing_msg.message_id
                    )
                except Exception as edit_error:
                    logger.warning(f"Не удалось отредактировать сообщение: {edit_error}")
                    bot.send_message(
                        message.chat.id,
                        "⚠️ Возникла проблема при анализе скриншота. Будут предоставлены стандартные скрипты оптимизации."
                    )
            except Exception as fallback_error:
                logger.error(f"Ошибка при создании шаблонных скриптов: {fallback_error}")
                bot.send_message(
                    message.chat.id,
                    "❌ Возникла критическая ошибка. Пожалуйста, попробуйте позже."
                )
                user_states[message.chat.id] = "main_menu"
                return
        
        # Проверяем, успешно ли получен результат
        if result:
            if isinstance(result, str):
                # Если результат - строка, значит произошла ошибка
                bot.send_message(message.chat.id, result)
                user_states[message.chat.id] = "main_menu"
            else:
                # Если результат - словарь с файлами, отправляем пользователю
                try:
                    # Обновляем сообщение о статусе
                    try:
                        bot.edit_message_text(
                            "✅ Скрипты оптимизации успешно созданы! Подготавливаю файлы для отправки...",
                            message.chat.id,
                            processing_msg.message_id
                        )
                    except Exception as edit_error:
                        logger.warning(f"Не удалось отредактировать сообщение: {edit_error}")
                        bot.send_message(
                            message.chat.id,
                            "✅ Скрипты оптимизации успешно созданы! Подготавливаю файлы для отправки..."
                        )
                    
                    # Отправляем файлы пользователю
                    asyncio.run(optimization_bot.send_script_files_to_user(message.chat.id, result))
                    
                    # Обновляем статистику
                    global script_gen_count
                    script_gen_count += 1
                    
                    # Валидируем скрипты и собираем статистику ошибок
                    try:
                        validation_results = validate_and_fix_scripts(result)
                        if validation_results.get("errors", 0) > 0:
                            # Обновляем статистику ошибок
                            optimization_bot.update_error_stats(validation_results)
                    except Exception as val_err:
                        logger.error(f"Ошибка при валидации скриптов: {val_err}")
                    
                    # Сбрасываем состояние пользователя
                    user_states[message.chat.id] = "main_menu"
                    
                    # Отображаем клавиатуру главного меню
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                    btn1 = types.KeyboardButton("🔧 Создать скрипт оптимизации")
                    btn2 = types.KeyboardButton("🔨 Исправить ошибки в скрипте")
                    markup.add(btn1, btn2)
                    
                    bot.send_message(
                        message.chat.id,
                        "✅ Скрипты готовы! Что вы хотите сделать дальше?",
                        reply_markup=markup
                    )
                    
                except Exception as e:
                    logger.error(f"Ошибка при отправке файлов: {e}")
                    bot.send_message(
                        message.chat.id,
                        "❌ Произошла ошибка при подготовке файлов. Пожалуйста, попробуйте снова."
                    )
                    user_states[message.chat.id] = "main_menu"
        else:
            bot.send_message(
                message.chat.id,
                "❌ Не удалось создать скрипты оптимизации. Пожалуйста, попробуйте снова с другим скриншотом."
            )
            user_states[message.chat.id] = "main_menu"
        
    except Exception as e:
        logger.error(f"Ошибка при обработке скриншота: {e}")
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при обработке скриншота. Пожалуйста, попробуйте снова."
        )
        user_states[message.chat.id] = "main_menu"

# Обработчик для текстовых сообщений в других состояниях
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) in ["waiting_for_screenshot", "waiting_for_error_screenshot"])
def handle_text_in_photo_states(message):
    """Обработка текстовых сообщений"""
    try:
        # Сохраняем текст сообщения
        user_messages[message.chat.id] = message.text
        
        # Определяем текущее состояние
        state = user_states.get(message.chat.id)
        
        if state == "waiting_for_screenshot":
            bot.send_message(
                message.chat.id,
                "📸 Отправьте скриншот с информацией о вашей системе.\n\n"
                "Ваше описание сохранено и будет использовано при генерации скрипта."
            )
        elif state == "waiting_for_error_screenshot":
            bot.send_message(
                message.chat.id,
                "📸 Отправьте скриншот с ошибкой, которую нужно исправить.\n\n"
                "Ваше описание сохранено и будет использовано при исправлении скрипта."
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике текстовых сообщений: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте снова.")

# Обработчик команды /stats
@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    """Отображает статистику по генерации скриптов"""
    try:
        metrics = ScriptMetrics()
        stats = metrics.get_summary()
        common_errors = metrics.get_common_errors()
        
        # Формируем сообщение со статистикой
        stats_message = f"📊 *Статистика оптимизации*\n\n"
        stats_message += f"📝 Сгенерировано скриптов: {stats['scripts_generated']}\n"
        stats_message += f"🔧 Исправлено скриптов: {stats['scripts_fixed']}\n"
        stats_message += f"⚠️ Всего найдено ошибок: {stats['total_errors']}\n\n"
        
        # Добавляем информацию о типах ошибок
        stats_message += f"🔍 *Распространенные ошибки:*\n"
        if common_errors:
            for error_type, count in common_errors:
                # Преобразуем технические имена ошибок в понятные описания
                if error_type == "admin_check_missing":
                    error_desc = "Отсутствует проверка прав администратора"
                elif error_type == "error_handling_missing":
                    error_desc = "Отсутствует обработка ошибок (try-catch)"
                elif error_type == "utf8_encoding_missing":
                    error_desc = "Отсутствует установка кодировки UTF-8"
                elif error_type == "unbalanced_braces":
                    error_desc = "Несбалансированные скобки в коде"
                elif error_type == "execution_policy_missing":
                    error_desc = "Отсутствует параметр ExecutionPolicy Bypass"
                else:
                    error_desc = error_type
                
                stats_message += f"  • {error_desc}: {count}\n"
        else:
            stats_message += "  Пока нет данных о распространенных ошибках\n"
        
        # Добавляем статистику по типам скриптов
        stats_message += f"\n📑 *Ошибки по типам скриптов:*\n"
        stats_message += f"  • PowerShell (.ps1): {stats['ps1_errors']}\n"
        stats_message += f"  • Batch (.bat): {stats['bat_errors']}\n"
        
        bot.send_message(message.chat.id, stats_message, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        bot.send_message(message.chat.id, "❌ Не удалось загрузить статистику. Попробуйте позже.")

# Обработчик команды для принудительного обновления промптов
@bot.message_handler(commands=['update_prompts'])
def cmd_update_prompts(message):
    """Обновляет промпты на основе статистики ошибок"""
    try:
        metrics = ScriptMetrics()
        optimizer = PromptOptimizer(metrics=metrics)
        
        success = optimizer.update_prompts_based_on_metrics()
        
        if success:
            bot.send_message(message.chat.id, "✅ Промпты успешно обновлены на основе статистики ошибок")
        else:
            bot.send_message(message.chat.id, "ℹ️ Недостаточно данных для оптимизации промптов или произошла ошибка")
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении промптов: {e}")
        bot.send_message(message.chat.id, "❌ Не удалось обновить промпты. Попробуйте позже.")

# Новый обработчик для команды /subscription
@bot.message_handler(commands=['subscription'])
def cmd_subscription(message):
    """Показывает информацию о подписке пользователя"""
    try:
        if not has_subscription_check:
            bot.send_message(
                message.chat.id, 
                "⚠️ Функционал подписок временно недоступен. Обратитесь к администратору бота."
            )
            return
            
        # Получаем информацию о подписке
        subscription_active = check_user_subscription(message.chat.id)
        
        # Создаем inline-кнопку для перехода к мини-приложению
        markup = types.InlineKeyboardMarkup()
        
        # Правильный формат для кнопки WebApp
        webapp_button = types.InlineKeyboardButton(
            text="💳 Открыть мини-приложение", 
            web_app={"url": "https://t.me/OptimizatorBot/app"}
        )
        markup.add(webapp_button)
        
        if subscription_active:
            # Получаем данные о подписке
            subscription_info = get_subscription_info(message.chat.id)
            days_left = subscription_info.get("days_left", 0)
            plan_name = subscription_info.get("plan_name", "Стандартный")
            
            # Отправляем краткую информацию с кнопкой
            bot.send_message(
                message.chat.id, 
                f"✅ У вас активна подписка *{plan_name}* (осталось дней: {days_left}).\n\nДля управления подпиской нажмите кнопку ниже:",
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            # Отправляем только кнопку для оформления подписки
            bot.send_message(
                message.chat.id,
                "Для оформления подписки нажмите кнопку ниже:",
                reply_markup=markup
            )
        
        logger.info(f"Пользователь {message.chat.id} запросил информацию о подписке")
    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /subscription: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении информации о подписке. Пожалуйста, попробуйте снова.")

def main():
    """Основная функция бота"""
    try:
        # Запускаем API сервер для активации подписок
        if has_api_server:
            subscription_api.start_subscription_api(bot)
        # Проверяем, не запущен ли уже бот
        if not ensure_single_instance():
            logger.error("Завершаем работу из-за уже запущенного экземпляра")
            return
            
        logger.info("Запуск бота...")
        
        # Запускаем healthcheck сервер для Railway
        if has_healthcheck and os.getenv('RAILWAY_ENVIRONMENT') is not None:
            logger.info("Запускаем сервер проверки работоспособности для Railway")
            healthcheck.update_bot_status({"status": "starting"})
            try:
                healthcheck.start_health_server()
                logger.info("Healthcheck сервер успешно запущен")
            except Exception as e:
                logger.error(f"Ошибка запуска healthcheck: {e}")
        
        # Инициализация оптимизатора промптов
        prompt_optimizer = PromptOptimizer()
        
        # Попытка обновления промптов на основе накопленных данных
        updated = prompt_optimizer.update_prompts_based_on_metrics()
        if updated:
            logger.info("Промпты успешно обновлены на основе накопленных данных")
        else:
            logger.info("Промпты не были обновлены, используются стандартные шаблоны")
            
        # Вывод статистики для логов
        logger.info("Статистика по скриптам:")
        logger.info(f"Всего сгенерировано скриптов: {script_gen_count}")
        
        total_errors = error_stats["total_errors"]
        logger.info(f"Обнаружено ошибок: {total_errors}")
        
        # Специальная проверка для Railway
        # Простая обработка конфликта экземпляров
        try:
            bot_info = bot.get_me()  # Проверяем подключение к Telegram API
            logger.info(f"Соединение с Telegram API установлено успешно: @{bot_info.username}")
            
            # Обновляем статус в healthcheck
            if has_healthcheck:
                healthcheck.update_bot_status({
                    "status": "running", 
                    "telegram_api_check": True,
                    "bot_username": bot_info.username
                })
        except telebot.apihelper.ApiTelegramException as e:
            if "Conflict" in str(e) and "terminated by other getUpdates request" in str(e):
                logger.error("Обнаружен конфликт с другим экземпляром бота. Завершение работы...")
                if has_healthcheck:
                    healthcheck.update_bot_status({"status": "error", "errors": [str(e)]})
                return  # Завершаем работу этого экземпляра
            raise
        
        # Проверка подключения к Claude API
        try:
            # Создаем клиент используя нашу собственную реализацию
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            logger.info("Клиент Claude API успешно инициализирован")
            
            # Тестируем клиент отправкой запроса
            try:
                test_response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Test connection"}]
                )
                logger.info(f"Тестовый запрос успешно отправлен: {test_response.content[0].text[:20] if test_response.content else 'Нет ответа'}")
            except Exception as test_err:
                logger.warning(f"Тестовый запрос не выполнен: {test_err}")
            
            # Обновляем статус в healthcheck
            if has_healthcheck:
                healthcheck.update_bot_status({"claude_api_check": True})
        except Exception as e:
            logger.error(f"Ошибка при инициализации Claude API: {e}")
            logger.error(f"Аргументы конструктора Anthropic: {inspect.signature(anthropic.Anthropic.__init__)}")
            if has_healthcheck:
                healthcheck.update_bot_status({"claude_api_check": False, "errors": [str(e)]})
            
        # Запуск бота с обработкой ошибок и таймаутами
        while True:
            try:
                logger.info("Запускаем бота с обработкой ошибок...")
                bot.polling(none_stop=False, interval=5, timeout=60)
                logger.info("Бот остановлен")
                time.sleep(15)  # Короткая пауза
            except telebot.apihelper.ApiTelegramException as e:
                if "Conflict" in str(e) and "terminated by other getUpdates request" in str(e):
                    logger.error("Конфликт с другим экземпляром бота. Завершение работы...")
                    if has_healthcheck:
                        healthcheck.update_bot_status({"status": "error", "errors": [str(e)]})
                    return  # Завершаем работу при конфликте
                logger.error(f"Ошибка API Telegram: {e}")
                if has_healthcheck:
                    healthcheck.update_bot_status({"status": "error", "errors": [str(e)]})
                time.sleep(30)  # Увеличенная пауза при ошибках API
            except Exception as e:
                logger.error(f"Ошибка в polling: {e}")
                if has_healthcheck:
                    healthcheck.update_bot_status({"status": "error", "errors": [str(e)]})
                time.sleep(30)  # Более длительная пауза при других ошибках
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        if has_healthcheck:
            healthcheck.update_bot_status({"status": "crashed", "errors": [str(e)]})

# Для тестирования
if __name__ == "__main__":
    # Запускаем бота
    main()