#!/usr/bin/env python
"""
API сервер для обработки запросов на активацию подписок
Этот модуль обрабатывает запросы от платежной системы и активирует подписки в боте
"""

import os
import logging
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging
from subscription_check import SubscriptionManager
import random
import string

# Загружаем переменные окружения
load_dotenv()

# Проверяем режим работы (тестовый или боевой)
IS_TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импортируем модуль проверки подписок
try:
    from subscription_check import SubscriptionManager
    has_subscription_check = True
except ImportError:
    has_subscription_check = False
    logger.error("ВНИМАНИЕ: Модуль проверки подписок не найден, функционал подписок отключен")

# Создаем Flask приложение для API эндпоинтов
app = Flask(__name__)

# Глобальная переменная для хранения ссылки на бота
bot_instance = None

def set_bot_instance(bot):
    """
    Устанавливает глобальную ссылку на экземпляр бота
    
    Args:
        bot: Экземпляр бота Telegram
    """
    global bot_instance
    bot_instance = bot
    logger.info("Экземпляр бота успешно установлен в API сервере")

@app.route('/health', methods=['GET'])
def health_check():
    """
    Эндпоинт для проверки работоспособности API
    """
    return jsonify({
        'status': 'ok',
        'subscription_module': has_subscription_check,
        'bot_connected': bot_instance is not None
    })

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    """
    Создание платежа через YooKassa
    """
    try:
        data = request.json
        logger.info(f"Получен запрос на создание платежа: {data}")
        
        required_fields = ['amount', 'planName', 'userId']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Отсутствует обязательное поле: {field}'
                }), 400
        
        # Проверяем тестовый режим
        test_result = check_test_mode(data)
        if test_result:
            return jsonify(test_result)
        
        # В реальном режиме создаем платеж через YooKassa
        return jsonify({
            'success': True,
            'orderId': generate_test_id('order_'),  # В реальности будет ID от YooKassa
            'paymentUrl': 'https://yookassa.ru/payment'  # В реальности будет URL от YooKassa
        })
    except Exception as e:
        return handle_error(e)

@app.route('/api/payment-status/<order_id>', methods=['GET'])
def get_payment_status(order_id):
    """
    Получение статуса платежа
    """
    try:
        logger.info(f"Получен запрос статуса платежа: {order_id}")
        
        # Проверяем тестовый режим
        test_result = check_test_mode({})
        if test_result:
            return jsonify(test_result)
        
        # В реальном режиме проверяем статус через YooKassa
        return jsonify({
            'success': True,
            'status': 'pending',  # В реальности будет статус от YooKassa
            'paymentId': generate_test_id('payment_')  # В реальности будет ID платежа от YooKassa
        })
    except Exception as e:
        return handle_error(e)

@app.route('/api/activate-subscription', methods=['POST'])
def activate_subscription():
    """
    Активация подписки после успешной оплаты
    """
    try:
        data = request.json
        logger.info(f"Получен запрос на активацию подписки: {data}")
        
        required_fields = ['userId', 'paymentId', 'planName']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Отсутствует обязательное поле: {field}'
                }), 400
        
        # Проверяем тестовый режим
        if IS_TEST_MODE:
            # В тестовом режиме всегда активируем подписку успешно
            return jsonify({
                'success': True,
                'message': 'Подписка успешно активирована (тестовый режим)'
            })
        
        # В реальном режиме проверяем подписку через YooKassa
        if has_subscription_check:
            success = add_user_subscription(
                data['userId'],
                data['planName'],
                30,  # Продолжительность в днях
                data['paymentId']
            )
            
            if success:
                # Отправляем уведомление пользователю
                if bot_instance:
                    try:
                        bot_instance.send_message(
                            chat_id=data['userId'],
                            text="✅ Ваша подписка успешно активирована!\n\n"  
                                 f"*План:* {data['planName']}\n"  
                                 f"*Срок действия:* 30 дней\n\n"  
                                 f"Теперь вы можете использовать все функции бота.",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при отправке уведомления: {e}")
                
                return jsonify({
                    'success': True,
                    'message': 'Подписка успешно активирована'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Не удалось активировать подписку'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'Модуль проверки подписок недоступен'
            }), 500
    except Exception as e:
        return handle_error(e)

@app.route('/add_subscription', methods=['POST'])
def add_subscription_api():
    """
    API эндпоинт для активации подписки после оплаты
    Принимает POST запросы от платежной системы
    """
    try:
        data = request.json
        logger.info(f"Получен запрос на активацию подписки: {data}")
        
        # Проверяем наличие необходимых полей в запросе
        required_fields = ['user_id', 'plan_name', 'payment_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Отсутствует обязательное поле: {field}'
                }), 400
        
        # Устанавливаем значения по умолчанию
        user_id = str(data['user_id'])
        plan_name = data.get('plan_name', 'Стандарт')
        duration_days = int(data.get('duration_days', 30))
        payment_id = data.get('payment_id')
        
        # Вызываем функцию добавления подписки
        if has_subscription_check:
            success = add_user_subscription(user_id, plan_name, duration_days, payment_id)
            
            if success:
                # Получаем информацию о подписке для ответа
                subscription_info = get_subscription_info(user_id)
                
                # Отправляем уведомление пользователю о успешной активации подписки
                if bot_instance:
                    try:
                        bot_instance.send_message(
                            chat_id=user_id,
                            text=f"✅ Ваша подписка успешно активирована!\n\n"  
                                 f"*План:* {plan_name}\n"  
                                 f"*Срок действия:* {subscription_info.get('days_left', duration_days)} дней\n\n"  
                                 f"Теперь вы можете использовать все функции бота.",
                            parse_mode="Markdown"
                        )
                        logger.info(f"Отправлено уведомление пользователю {user_id} об активации подписки")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
                else:
                    logger.warning("Невозможно отправить уведомление: экземпляр бота не инициализирован")
                
                return jsonify({
                    'success': True,
                    'message': 'Подписка успешно активирована',
                    'expires_at': subscription_info.get('expires_at', 0),
                    'expires_at_formatted': subscription_info.get('expires_at_formatted', ''),
                    'days_left': subscription_info.get('days_left', duration_days)
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Не удалось активировать подписку'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'Модуль проверки подписок недоступен'
            }), 500
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса на активацию подписки: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def run_api_server():
    """
    Запускает API сервер в отдельном потоке
    """
    # Получаем порт из переменной окружения или используем порт по умолчанию
    api_port = int(os.getenv('BOT_API_PORT', 5000))
    
    # Запускаем Flask приложение
    logger.info(f"Запуск API сервера на порту {api_port}")
    app.run(host='0.0.0.0', port=api_port)

def start_subscription_api(bot=None):
    """
    Запускает API сервер в отдельном потоке
    
    Args:
        bot: Экземпляр бота Telegram (опционально)
    """
    if bot:
        set_bot_instance(bot)
    
    # Запускаем API сервер в отдельном потоке
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    logger.info(f"API сервер для подписок запущен на порту {os.getenv('BOT_API_PORT', 5000)}")
    
    return api_thread

# Для тестирования
if __name__ == "__main__":
    # Запускаем API сервер напрямую для тестирования
    run_api_server()
