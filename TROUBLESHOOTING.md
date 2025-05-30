# Руководство по устранению неполадок

## Проблемы с API Anthropic

### Ошибки совместимости версий

Библиотека Anthropic несколько раз меняла свой API, что привело к несовместимостям между разными версиями. В нашем проекте могут возникнуть две основные ошибки:

1. **'Anthropic' object has no attribute 'messages'**
   - **Причина**: Код использует новый API (messages), но установлена старая версия библиотеки
   - **Решение**: Установить новую версию библиотеки (anthropic==0.19.0)

2. **'Anthropic' object has no attribute 'completion'**
   - **Причина**: Код использует старый API (completion), но установлена новая версия библиотеки
   - **Решение**: Установить новую версию библиотеки (anthropic==0.19.0) и убедиться, что в коде используется метод messages.create

### ВАЖНО: В текущей версии проекта используется новый API (messages.create)

В текущей версии проекта используется библиотека **anthropic версии 0.19.0** и вызовы API через метод **messages.create**. Убедитесь, что в файле requirements.txt этот выбор отражен корректно, и библиотека установлена:

```bash
pip install anthropic==0.19.0
```

### Проверка совместимости API

Для проверки совместимости API запустите скрипт:
```bash
python check_anthropic.py
```

Скрипт выведет информацию о текущей версии библиотеки, доступных методах API и рекомендуемых действиях.

### Ручное исправление при использовании неправильной версии библиотеки

Если вы видите ошибку 'Anthropic' object has no attribute 'messages', это означает, что установлена старая версия библиотеки. Выполните следующие шаги:

1. Установите версию 0.19.0:
   ```bash
   pip install anthropic==0.19.0
   ```

2. Проверьте установленную версию:
   ```bash
   pip show anthropic
   ```

3. Запустите скрипт проверки API:
   ```bash
   python check_anthropic.py
   ```

4. Убедитесь, что в файле `requirements.txt` указана версия 0.19.0 и закомментирована строка с версией 0.5.0.

5. Перезапустите бота:
   ```bash
   python optimization_bot.py
   ```

### Диагностика ошибок

| Ошибка | Возможная причина | Решение |
|--------|-------------------|---------|
| 'Anthropic' object has no attribute 'messages' | Установлена старая версия библиотеки | Установите anthropic==0.19.0 |
| 'Anthropic' object has no attribute 'completion' | Код использует устаревший метод API | Обновите код для использования messages.create |
| Access denied | Неправильный API ключ | Проверьте ANTHROPIC_API_KEY в файле .env |
| Connection error | Проблемы с сетью | Проверьте подключение к интернету и настройки файрвола |

### Проверка ANTHROPIC_API_KEY

API ключ должен быть указан в файле `.env` в следующем формате:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Чтобы проверить, правильно ли считывается ключ, выполните:

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"API ключ: {api_key[:10]}...")  # Показываем только начало ключа для безопасности
```

### Переключение на старый API (не рекомендуется)

Если по какой-то причине вам необходимо использовать старый API (completion), нужно внести существенные изменения в код:

1. Установите старую версию библиотеки:
   ```bash
   pip install anthropic==0.5.0
   ```

2. Обновите файл requirements.txt, закомментировав строку с версией 0.19.0 и раскомментировав строку с версией 0.5.0.

3. Измените все вызовы API в коде `optimization_bot.py`, заменив messages.create на completion.

Этот подход не рекомендуется, так как старый API может быть устаревшим и перестать работать в будущем. 