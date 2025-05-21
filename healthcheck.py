"""
Простой веб-сервер для проверки состояния бота в Railway.
Запускается автоматически вместе с ботом в Railway.
"""

import os
import logging
import threading
import time
from flask import Flask, jsonify, request

# Импортируем функции для работы с подписками
try:
    from subscription_check import add_user_subscription, get_subscription_info
    has_subscription_module = True
except ImportError:
    has_subscription_module = False
    logging.error("Не удалось импортировать модуль подписок в healthcheck.py")

# Конфигурация логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

# Глобальный статус бота
bot_status = {
    "status": "initializing",
    "started_at": time.time(),
    "errors": [],
    "telegram_api_check": None,
    "claude_api_check": None
}

@app.route('/')
def home():
    """Главная страница с базовой информацией о статусе"""
    return jsonify({
        "name": "Windows Optimization Bot",
        "status": bot_status["status"],
        "uptime": int(time.time() - bot_status["started_at"]),
        "railway_environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown")
    })

@app.route('/health')
def health():
    """Полная информация о состоянии бота"""
    is_healthy = bot_status["status"] == "running" and not bot_status["errors"]
    
    return jsonify({
        "status": "healthy" if is_healthy else "unhealthy",
        "details": bot_status,
        "environment": {
            "railway": bool(os.getenv("RAILWAY_ENVIRONMENT")),
            "telegram_token": bool(os.getenv("TELEGRAM_TOKEN")),
            "anthropic_key": bool(os.getenv("ANTHROPIC_API_KEY")),
            "python_version": os.getenv("PYTHON_VERSION", "unknown")
        }
    }), 200 if is_healthy else 503

@app.route('/add_subscription', methods=['POST'])
def add_subscription():
    """API-эндпоинт для активации подписки после оплаты"""
    if not has_subscription_module:
        logger.error("Модуль подписок не доступен, невозможно активировать подписку")
        return jsonify({
            "success": False,
            "message": "Модуль подписок не установлен на сервере"
        }), 500
        
    try:
        # Получаем данные из запроса
        data = request.json
        
        if not data:
            return jsonify({
                "success": False,
                "message": "Отсутствуют данные в запросе"
            }), 400
            
        # Проверяем обязательные поля
        required_fields = ['user_id', 'plan_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "message": f"Отсутствует обязательное поле: {field}"
                }), 400
        
        # Получаем параметры подписки
        user_id = data['user_id']
        plan_name = data['plan_name']
        duration_days = data.get('duration_days', 30)  # По умолчанию 30 дней
        payment_id = data.get('payment_id', 'external_payment')
        
        # Активируем подписку
        logger.info(f"Активация подписки для пользователя {user_id}, план: {plan_name}, срок: {duration_days} дней")
        success = add_user_subscription(user_id, plan_name, duration_days, payment_id)
        
        if success:
            # Получаем информацию о подписке для ответа
            subscription_info = get_subscription_info(user_id)
            
            return jsonify({
                "success": True,
                "message": "Подписка успешно активирована",
                "subscription": subscription_info
            })
        else:
            return jsonify({
                "success": False,
                "message": "Не удалось активировать подписку"
            }), 500
            
    except Exception as e:
        logger.error(f"Ошибка при активации подписки: {e}")
        return jsonify({
            "success": False,
            "message": f"Ошибка при обработке запроса: {str(e)}"
        }), 500

def update_bot_status(new_status):
    """Функция для обновления статуса бота из основного процесса"""
    bot_status.update(new_status)

def start_health_server():
    """Запускает веб-сервер для проверки состояния в отдельном потоке"""
    port = int(os.getenv("PORT", 8080))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False)).start()
    logger.info(f"Healthcheck server started on port {port}")

if __name__ == "__main__":
    # При запуске напрямую запускаем сервер на порту 8080
    app.run(host="0.0.0.0", port=8080, debug=True) 