"""
Простой веб-сервер для проверки состояния бота в Railway.
Запускается автоматически вместе с ботом в Railway.
"""

import os
import logging
import threading
import time
from flask import Flask, jsonify

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