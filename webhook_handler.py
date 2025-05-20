#!/usr/bin/env python
"""
Обработчик webhook-уведомлений от сервера монетизации
Запускается как отдельный микро-сервис для приема уведомлений об оплате
"""

import os
import json
import logging
import hmac
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

# Импортируем модуль для управления подписками
try:
    from subscription_check import add_user_subscription, check_user_subscription, get_subscription_info
    has_subscription_module = True
except ImportError:
    has_subscription_module = False
    print("ПРЕДУПРЕЖДЕНИЕ: Модуль subscription_check не найден. Подписки не будут обрабатываться.")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация Flask-приложения
app = Flask(__name__)

# Секретный ключ для верификации вебхуков
# В реальном окружении должен быть загружен из переменных окружения
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your_webhook_secret_key_here')

# План подписок и их продолжительность в днях
SUBSCRIPTION_PLANS = {
    'basic': 30,       # Базовый план на 1 месяц
    'standard': 30,    # Стандартный план на 1 месяц
    'premium': 90      # Премиум план на 3 месяца
}

# Функция для верификации подписи вебхука
def verify_webhook_signature(signature, data):
    """
    Проверяет подпись вебхука от сервера монетизации
    
    Args:
        signature (str): Значение заголовка X-Webhook-Signature
        data (bytes): Тело запроса в байтах
        
    Returns:
        bool: True, если подпись действительна
    """
    if not signature or not WEBHOOK_SECRET:
        return False
    
    # Создаем HMAC с SHA-256
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(), 
        data, 
        hashlib.sha256
    ).hexdigest()
    
    # Проверяем соответствие сигнатур
    return hmac.compare_digest(expected_signature, signature)

@app.route('/', methods=['GET'])
def home():
    """
    Домашняя страница для проверки работоспособности сервиса
    """
    return jsonify({
        "status": "ok",
        "message": "Webhook handler is running",
        "subscription_module": has_subscription_module
    })

@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    """
    Обработчик вебхука для уведомлений об оплате
    """
    try:
        logger.info("Получен webhook запрос от сервера монетизации")
        
        # Получаем сигнатуру из заголовка
        signature = request.headers.get('X-Webhook-Signature')
        
        # Получаем данные запроса
        request_data = request.get_data()
        
        # Проверяем подпись (при необходимости)
        if signature and not verify_webhook_signature(signature, request_data):
            logger.warning("Неверная подпись webhook")
            return jsonify({"status": "error", "message": "Invalid signature"}), 403
        
        # Парсим данные JSON
        data = request.json
        logger.info(f"Получены данные webhook: {data}")
        
        # Проверяем наличие необходимых полей
        if not data or 'event' not in data:
            logger.warning("Отсутствуют необходимые поля в запросе webhook")
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
        # Обрабатываем уведомление о платеже
        if data['event'] == 'payment.succeeded':
            # Проверяем наличие модуля подписок
            if not has_subscription_module:
                logger.error("Модуль подписок не доступен, невозможно обработать платеж")
                return jsonify({"status": "error", "message": "Subscription module not available"}), 500
            
            # Извлекаем данные о платеже
            payment_id = data.get('payment_id') or data.get('orderId')
            user_id = data.get('metadata', {}).get('userId')
            plan_name = data.get('metadata', {}).get('planName', 'standard')
            
            if not payment_id or not user_id:
                logger.warning("Отсутствует ID платежа или ID пользователя в данных webhook")
                return jsonify({"status": "error", "message": "Missing payment_id or user_id"}), 400
            
            # Определяем продолжительность подписки на основе плана
            duration_days = SUBSCRIPTION_PLANS.get(plan_name.lower(), 30)
            
            # Добавляем или обновляем подписку пользователя
            success = add_user_subscription(
                user_id=user_id, 
                plan_name=plan_name, 
                duration_days=duration_days, 
                payment_id=payment_id
            )
            
            if success:
                logger.info(f"Успешно добавлена подписка для пользователя {user_id}, план {plan_name}, "
                           f"продолжительность {duration_days} дней, платеж {payment_id}")
                return jsonify({
                    "status": "success", 
                    "message": "Subscription added successfully",
                    "user_id": user_id,
                    "plan": plan_name,
                    "duration_days": duration_days,
                    "expires_at": (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                logger.error(f"Не удалось добавить подписку для пользователя {user_id}")
                return jsonify({"status": "error", "message": "Failed to add subscription"}), 500
                
        # Обрабатываем другие типы событий при необходимости
        elif data['event'] == 'payment.canceled':
            logger.info(f"Платеж отменен: {data}")
            return jsonify({"status": "success", "message": "Payment cancellation noted"})
            
        else:
            logger.info(f"Неизвестный тип события: {data['event']}")
            return jsonify({"status": "success", "message": "Event noted but not processed"})
            
    except Exception as e:
        logger.exception(f"Ошибка при обработке webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/check-subscription/<user_id>', methods=['GET'])
def check_subscription(user_id):
    """
    API для проверки статуса подписки пользователя
    
    Args:
        user_id (str): ID пользователя для проверки
        
    Returns:
        JSON с информацией о подписке
    """
    try:
        if not has_subscription_module:
            return jsonify({"error": "Subscription module not available"}), 500
            
        # Проверяем подписку
        has_subscription = check_user_subscription(user_id)
        
        # Получаем детали подписки
        subscription_info = get_subscription_info(user_id)
        
        return jsonify({
            "user_id": user_id,
            "has_active_subscription": has_subscription,
            "subscription_details": subscription_info or {}
        })
    except Exception as e:
        logger.exception(f"Ошибка при проверке подписки: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-subscription', methods=['POST'])
def add_subscription():
    """
    API для ручного добавления подписки пользователю
    (Защищено ключом, только для администраторов)
    
    Ожидаемые параметры:
        user_id: ID пользователя
        plan_name: Название плана подписки
        duration_days: Продолжительность подписки в днях
        api_key: Ключ API для авторизации
    """
    try:
        # Проверяем наличие модуля подписок
        if not has_subscription_module:
            return jsonify({"error": "Subscription module not available"}), 500
            
        # Получаем данные из запроса
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Получаем API ключ из запроса
        api_key = data.get('api_key')
        
        # Проверяем API ключ (простая проверка для примера)
        if not api_key or api_key != os.getenv('ADMIN_API_KEY', 'admin_secret_key'):
            return jsonify({"error": "Invalid API key"}), 403
            
        # Получаем необходимые параметры
        user_id = data.get('user_id')
        plan_name = data.get('plan_name', 'standard')
        duration_days = int(data.get('duration_days', 30))
        
        if not user_id:
            return jsonify({"error": "Missing user_id parameter"}), 400
            
        # Добавляем подписку
        success = add_user_subscription(
            user_id=user_id,
            plan_name=plan_name,
            duration_days=duration_days,
            payment_id=f"manual_add_{datetime.now().timestamp()}"
        )
        
        if success:
            logger.info(f"Вручную добавлена подписка для пользователя {user_id}, "
                       f"план {plan_name}, продолжительность {duration_days} дней")
                       
            return jsonify({
                "status": "success",
                "message": "Subscription added successfully",
                "user_id": user_id,
                "plan": plan_name,
                "duration_days": duration_days,
                "expires_at": (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return jsonify({"error": "Failed to add subscription"}), 500
            
    except Exception as e:
        logger.exception(f"Ошибка при добавлении подписки: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Запускаем Flask-приложение
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    # Логируем информацию о запуске
    logger.info(f"Запуск webhook обработчика на {host}:{port}")
    logger.info(f"Модуль подписок доступен: {has_subscription_module}")
    
    # Запускаем сервер с поддержкой перезагрузки в режиме разработки
    app.run(host=host, port=port, debug=os.getenv('DEBUG', 'false').lower() == 'true') 