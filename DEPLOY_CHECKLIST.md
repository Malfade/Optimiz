# Чеклист файлов для деплоя в Railway

## Основные файлы

- [ ] `main.py` - обновленный с импортом fix_imports
- [ ] `fix_imports.py` - система патчинга импортов
- [ ] `fallback_anthropic.py` - минимальная реализация API Anthropic
- [ ] `safe_anthropic.py` - обновленная безопасная обертка
- [ ] `optimization_bot.py` - основной код бота
- [ ] `requirements.txt` - без зависимости от anthropic
- [ ] `Procfile` - команда запуска для Railway

## Дополнительные файлы

- [ ] `test_fix_import.py` - для проверки корректности импортов
- [ ] `RAILWAY_RESTART.md` - инструкция по перезапуску
- [ ] `RAILWAY_DEPLOY_NEW.md` - новая инструкция по деплою
- [ ] `MIGRATION_GUIDE.md` - руководство по миграции

## Файлы, которые можно архивировать

- [ ] `fix_railway_anthropic.py`
- [ ] `anthropic_wrapper.py`
- [ ] `test_import_anthropic.py`
- [ ] `test_railway_fix.py`
- [ ] `direct_fix.py`
- [ ] `test_all_fixes.py`
- [ ] `fix_railway_proxies.bat`
- [ ] `fix_railway_proxies.sh`
- [ ] `PROXIES_ISSUE_QUICKFIX.md`
- [ ] `railway_fix.py`
- [ ] `override_anthropic.py`

## Шаги перед деплоем

1. [ ] Проверка test_fix_import.py локально
2. [ ] Проверка отсутствия библиотеки anthropic в requirements.txt
3. [ ] Проверка наличия import fix_imports в main.py
4. [ ] Проверка актуальности safe_anthropic.py
5. [ ] Создание архивной копии старых файлов

## Шаги после деплоя

1. [ ] Проверка логов на наличие сообщений об успешной инициализации
2. [ ] Проверка работы бота в Telegram
3. [ ] Проверка обработки скриншотов и генерации скриптов

## Переменные окружения

- [ ] `API_KEY` - ключ API Anthropic
- [ ] `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- [ ] `ALLOWED_USERS` - (опционально) список разрешенных ID пользователей

## Дополнительно

- [ ] Сохранить ссылку на проект в Railway
- [ ] Настроить автоматические перезапуски (если необходимо)
- [ ] Настроить мониторинг (если необходимо) 