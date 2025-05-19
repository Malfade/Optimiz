# Руководство по миграции на fallback_anthropic

Это руководство описывает процесс миграции с предыдущего решения проблемы прокси на новый подход с использованием `fallback_anthropic`.

## Обзор изменений

Новое решение:
1. Использует собственную имплементацию API Anthropic без зависимости от официальной библиотеки
2. Внедряет механизм автоматического патчинга импортов через `sys.modules`
3. Имеет улучшенную обработку ошибок и логирование
4. Значительно упрощает развертывание на Railway

## Шаги миграции

### 1. Резервное копирование

Перед миграцией создайте резервную копию следующих файлов:
- `main.py`
- `safe_anthropic.py`
- `requirements.txt`

### 2. Удаление старых файлов для решения проблемы прокси

Следующие файлы больше не требуются:
- `fix_railway_anthropic.py`
- `anthropic_wrapper.py`
- `test_import_anthropic.py`
- `test_railway_fix.py`
- `direct_fix.py`
- `test_all_fixes.py`
- `fix_railway_proxies.bat`
- `fix_railway_proxies.sh`
- `PROXIES_ISSUE_QUICKFIX.md`
- `railway_fix.py`
- `override_anthropic.py`

Вы можете их архивировать или удалить.

### 3. Добавление новых файлов

Добавьте следующие новые файлы:
- `fix_imports.py` - система патчинга импортов
- `fallback_anthropic.py` - реализация API без зависимостей
- `test_fix_import.py` - тестовый скрипт для проверки импортов

### 4. Обновление существующих файлов

#### Обновление main.py

В начале файла `main.py` добавьте импорт `fix_imports`:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os

# Исправление импортов перед всеми другими импортами
import fix_imports

# Остальные импорты
import telebot
# ... остальной код
```

#### Обновление safe_anthropic.py

Обновите файл `safe_anthropic.py`, чтобы использовать `fallback_anthropic`:

```python
"""
Безопасная обертка для Anthropic API без зависимостей от оригинальной библиотеки.
"""

import logging
import os
from typing import Dict, Any, Optional

# Инициализация логирования
logger = logging.getLogger(__name__)

class SafeAnthropic:
    """Безопасная обертка для Anthropic API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Инициализация клиента с API ключом."""
        self.client = None
        self.api_key = api_key or os.environ.get("API_KEY", "")
        self.initialized = False
        
        try:
            import fallback_anthropic
            self.client = fallback_anthropic.Anthropic(api_key=self.api_key)
            self.initialized = True
            logger.info("SafeAnthropic клиент создан успешно.")
        except Exception as e:
            logger.error(f"Ошибка при инициализации SafeAnthropic: {e}")

def create_client(api_key: Optional[str] = None) -> SafeAnthropic:
    """
    Создает клиент Anthropic API с указанным ключом API.
    
    Args:
        api_key: Ключ API Anthropic. Если не указан, берется из переменной окружения API_KEY.
        
    Returns:
        Экземпляр SafeAnthropic.
    """
    client = SafeAnthropic(api_key)
    if not client.initialized:
        logger.warning("Не удалось создать клиент Anthropic. Проверьте API ключ и соединение.")
    else:
        logger.info(f"Клиент Anthropic создан успешно. Версия: 0.19.1-safe-fallback")
        print(f"Клиент Anthropic создан успешно. Версия: 0.19.1-safe-fallback")
    
    return client
```

#### Обновление requirements.txt

Удалите библиотеку `anthropic` из `requirements.txt`:

```
# Зависимости для Windows Optimization Bot
# Точные версии для обеспечения совместимости

# Telegram Bot API
pyTelegramBotAPI==4.15.0

# Асинхронный клиент HTTP
aiohttp==3.9.3
asyncio==3.4.3

# Работа с изображениями
pillow>=10.0.0

# Переменные окружения
python-dotenv==1.0.0

# HTTP-запросы
requests==2.31.0

# Логирование и диагностика
colorlog==6.8.0

# Flask для проверки работоспособности (опционально)
flask==2.3.3
```

### 5. Тестирование

Запустите тест `test_fix_import.py` для проверки работы импортов:

```bash
python test_fix_import.py
```

Вы должны увидеть сообщения об успешной инициализации и патчинге импортов.

### 6. Развертывание

Для развертывания на Railway следуйте инструкции в файле `RAILWAY_DEPLOY_NEW.md`.

## Проверка миграции

После миграции убедитесь, что:

1. Бот запускается без ошибок
2. В логах присутствуют сообщения об успешной инициализации модулей
3. Бот отвечает на сообщения в Telegram
4. Обработка скриншотов и генерация скриптов работает корректно

## Откат изменений

Если возникли проблемы, восстановите резервные копии файлов и вернитесь к предыдущему решению. 