#!/usr/bin/env python
"""
Модуль для проверки активных подписок пользователей
Интегрируется с сервером монетизации для проверки статуса оплаты
"""

import os
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Путь к файлу с данными о подписках пользователей
SUBSCRIPTIONS_FILE = Path(os.path.dirname(os.path.abspath(__file__))) / "subscriptions.json"

# URL сервера монетизации
# Используем размещенную на Railway платежную систему
default_payment_url = "https://paymentsysatem-production.up.railway.app"
MONETIZATION_SERVER_URL = os.getenv("PAYMENT_SYSTEM_URL", default_payment_url)

class SubscriptionManager:
    """
    Класс для управления подписками пользователей
    """
    
    def __init__(self):
        """
        Инициализация менеджера подписок
        """
        self.subscriptions = self._load_subscriptions()
        self.active_cache = {}  # Кеш для быстрой проверки активных подписок
        self._update_cache()
        
    def _load_subscriptions(self):
        """
        Загрузка данных о подписках из файла
        """
        try:
            if SUBSCRIPTIONS_FILE.exists():
                with open(SUBSCRIPTIONS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # Если файл не существует, создаем пустой словарь подписок
                return {"users": {}}
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных о подписках: {e}")
            return {"users": {}}
    
    def _save_subscriptions(self):
        """
        Сохранение данных о подписках в файл
        """
        try:
            with open(SUBSCRIPTIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.subscriptions, f, indent=2, ensure_ascii=False)
            # Обновляем кеш после сохранения
            self._update_cache()
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных о подписках: {e}")
            
    def _update_cache(self):
        """
        Обновление кеша активных подписок
        """
        self.active_cache = {}
        current_time = datetime.now().timestamp()
        
        # Debug log the current time for comparison
        logger.info(f"[DEBUG] Updating cache at timestamp: {current_time}, formatted: {datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')}")
        
        for user_id, subscription in self.subscriptions.get("users", {}).items():
            # Ensure user_id is string
            user_id = str(user_id)
            
            # Debug log for each subscription being processed
            expires_at = subscription.get("expires_at", 0)
            status = subscription.get("status")
            expires_formatted = datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S') if expires_at else "None"
            
            logger.info(f"[DEBUG] Processing cache for user {user_id}: status={status}, expires_at={expires_at} ({expires_formatted})")
            
            # Проверяем, что подписка активна (оплачена и не истекла)
            if status == "active" and expires_at > current_time:
                self.active_cache[user_id] = True
                logger.info(f"[DEBUG] User {user_id} marked as ACTIVE in cache")
            else:
                self.active_cache[user_id] = False
                logger.info(f"[DEBUG] User {user_id} marked as INACTIVE in cache: status={status}, expires check: {expires_at > current_time}")
    
    def add_subscription(self, user_id, plan_name, duration_days=30, payment_id=None, generations_limit=None):
        """
        Добавление новой подписки для пользователя
        
        Args:
            user_id (str): ID пользователя
            plan_name (str): Название плана подписки
            duration_days (int): Продолжительность подписки в днях
            payment_id (str): ID платежа в системе оплаты
            generations_limit (int): Лимит генераций для подписки
            
        Returns:
            bool: True, если подписка успешно добавлена
        """
        try:
            # Ensure user_id is a string
            user_id = str(user_id)
            logger.info(f"[DEBUG] Adding subscription for user ID: {user_id}, plan: {plan_name}, duration: {duration_days} days")
            
            # Определяем лимит генераций по плану, если не указан
            if generations_limit is None:
                generations_map = {
                    '1 скрипт': 1,
                    '3 скрипта': 3,
                    '10 скриптов': 10,
                    'single': 1,
                    'triple': 3,
                    'pack': 10
                }
                generations_limit = generations_map.get(plan_name, 1)
            
            # Проверяем статус платежа через API сервера монетизации
            if payment_id and not payment_id.startswith('test_'):
                payment_status_url = f"{MONETIZATION_SERVER_URL}/api/payment-status/{payment_id}"
                logger.info(f"[DEBUG] Checking payment status at {payment_status_url}")
                
                try:
                    response = requests.get(payment_status_url)
                    if response.status_code == 200:
                        payment_data = response.json()
                        logger.info(f"[DEBUG] Payment status response: {payment_data}")
                        
                        if payment_data.get('status') != 'succeeded':
                            logger.error(f"[DEBUG] Payment {payment_id} not succeeded: {payment_data.get('status')}")
                            return False
                    else:
                        logger.error(f"[DEBUG] Failed to check payment status: {response.status_code}")
                        return False
                except Exception as e:
                    logger.error(f"[DEBUG] Error checking payment status: {e}")
                    return False
            elif payment_id and payment_id.startswith('test_'):
                logger.info(f"[DEBUG] Skipping payment check for test payment: {payment_id}")
            
            # Создаем записи в структуре, если их еще нет
            if "users" not in self.subscriptions:
                self.subscriptions["users"] = {}
                
            # Получаем текущее время
            now = datetime.now()
            
            # Вычисляем дату окончания подписки
            expires_at = (now + timedelta(days=duration_days)).timestamp()
            
            # Debug log for the subscription data
            logger.info(f"[DEBUG] Subscription details: start={now.timestamp()}, expires={expires_at}, "  
                       f"formatted_start={now.strftime('%Y-%m-%d %H:%M:%S')}, "
                       f"formatted_end={datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Добавляем информацию о подписке с поддержкой генераций
            self.subscriptions["users"][user_id] = {
                "plan_name": plan_name,
                "status": "active",
                "created_at": now.timestamp(),
                "expires_at": expires_at,
                "payment_id": payment_id,
                "generations_limit": generations_limit,
                "generations_used": 0
            }
            
            # Log subscription data after addition
            logger.info(f"[DEBUG] Updated subscriptions data for user {user_id}: {self.subscriptions['users'].get(user_id)}")
            
            # Сохраняем данные и обновляем кеш
            self._save_subscriptions()
            
            # Manually update the active cache for this user to ensure it's immediately available
            self.active_cache[user_id] = True
            logger.info(f"[DEBUG] Manually updated active cache for user {user_id} to {self.active_cache.get(user_id)}")
            
            logger.info(f"Добавлена подписка для пользователя {user_id}, план {plan_name}, лимит генераций: {generations_limit}, " 
                       f"срок окончания: {datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении подписки для пользователя {user_id}: {e}")
            return False
    
    def has_active_subscription(self, user_id):
        """
        Проверка наличия активной подписки у пользователя
        
        Args:
            user_id (str): ID пользователя
            
        Returns:
            bool: True, если у пользователя есть активная подписка
        """
        # Преобразуем user_id в строку для единообразия
        original_user_id = user_id
        user_id = str(user_id)
        
        logger.info(f"[DEBUG] Checking active subscription for user ID: {original_user_id} (as string: {user_id})")
        
        # Сначала проверяем кеш для быстрого ответа
        if user_id in self.active_cache:
            cache_result = self.active_cache[user_id]
            logger.info(f"[DEBUG] Found user {user_id} in cache with value: {cache_result}")
            return cache_result
        
        # Log subscription data for debugging
        all_users = list(self.subscriptions.get("users", {}).keys())
        logger.info(f"[DEBUG] All users in subscription data: {all_users}")
        
        # Если пользователя нет в кеше, проверяем полностью
        if "users" not in self.subscriptions:
            logger.info(f"[DEBUG] No 'users' key in subscription data")
            return False
            
        if user_id not in self.subscriptions["users"]:
            logger.info(f"[DEBUG] User {user_id} not found in subscription data")
            return False
        
        subscription = self.subscriptions["users"][user_id]
        logger.info(f"[DEBUG] Found subscription data for user {user_id}: {subscription}")
        
        # Проверяем статус и срок действия подписки
        status = subscription.get("status")
        if status != "active":
            logger.info(f"[DEBUG] Subscription status is not active: {status}")
            return False
        
        current_time = datetime.now().timestamp()
        expires_at = subscription.get("expires_at", 0)
        
        logger.info(f"[DEBUG] Checking expiration: current_time={current_time}, expires_at={expires_at}, "  
                   f"formatted_current={datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')}, "  
                   f"formatted_expires={datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')}")
        
        if expires_at <= current_time:
            # Подписка истекла, обновляем ее статус
            logger.info(f"[DEBUG] Subscription has expired, updating status to 'expired'")
            subscription["status"] = "expired"
            self._save_subscriptions()
            return False
        
        # Update cache manually
        self.active_cache[user_id] = True
        logger.info(f"[DEBUG] Subscription is active, updating cache and returning True")
        return True
    
    def check_payment_status(self, payment_id):
        """
        Проверка статуса платежа через API сервера монетизации
        
        Args:
            payment_id (str): ID платежа
            
        Returns:
            bool: True, если платеж успешно завершен
        """
        # Если ID платежа начинается с 'test_', считаем его тестовым
        if payment_id and (payment_id.startswith('test_') or 'test' in payment_id.lower()):
            logger.info(f"Обнаружен тестовый платеж {payment_id}, автоматически подтверждаем")
            return True
            
        try:
            # Формируем URL для запроса статуса платежа
            url = f"{MONETIZATION_SERVER_URL}/api/payment-status/{payment_id}"
            
            # Отправляем запрос
            response = requests.get(url, timeout=10)
            
            # Проверяем ответ
            if response.status_code == 200:
                payment_data = response.json()
                logger.info(f"Получен статус платежа {payment_id}: {payment_data}")
                
                # Проверяем статус платежа
                if payment_data.get("status") == "succeeded":
                    return True
                # Поддержка тестовых платежей
                elif payment_data.get("status") == "test_succeeded" or payment_data.get("test") == True:
                    logger.info(f"Обнаружен успешный тестовый платеж {payment_id}")
                    return True
            elif response.status_code == 404:
                # Если платеж не найден, но URL содержит 'test', считаем его тестовым
                if 'test' in payment_id.lower():
                    logger.info(f"Платеж {payment_id} не найден, но похож на тестовый - подтверждаем")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса платежа {payment_id}: {e}")
            # Если произошла ошибка, но платеж похож на тестовый, подтверждаем его
            if payment_id and 'test' in payment_id.lower():
                logger.info(f"При ошибке обнаружен тестовый платеж {payment_id}, подтверждаем")
                return True
            return False

    def get_subscription_details(self, user_id):
        """
        Получение подробной информации о подписке пользователя
        
        Args:
            user_id (str): ID пользователя
            
        Returns:
            dict: Информация о подписке или None, если подписки нет
        """
        user_id = str(user_id)
        if "users" not in self.subscriptions or user_id not in self.subscriptions["users"]:
            return None
        
        subscription = self.subscriptions["users"][user_id]
        
        # Добавляем дополнительные поля с читаемыми датами
        if "created_at" in subscription:
            subscription["created_at_formatted"] = datetime.fromtimestamp(
                subscription["created_at"]).strftime('%Y-%m-%d %H:%M:%S')
        
        if "expires_at" in subscription:
            subscription["expires_at_formatted"] = datetime.fromtimestamp(
                subscription["expires_at"]).strftime('%Y-%m-%d %H:%M:%S')
            
            # Добавляем оставшиеся дни
            current_time = datetime.now().timestamp()
            if subscription["expires_at"] > current_time:
                days_left = (subscription["expires_at"] - current_time) / (60 * 60 * 24)
                subscription["days_left"] = round(days_left, 1)
            else:
                subscription["days_left"] = 0
        
        return subscription

    def can_generate_script(self, user_id):
        """
        Проверка возможности создания скрипта (есть ли доступные генерации)
        
        Args:
            user_id (str): ID пользователя
            
        Returns:
            bool: True, если пользователь может создать скрипт
        """
        user_id = str(user_id)
        
        # Сначала проверяем активную подписку
        if not self.has_active_subscription(user_id):
            return False
        
        # Получаем данные подписки
        subscription = self.subscriptions["users"].get(user_id)
        if not subscription:
            return False
        
        generations_limit = subscription.get("generations_limit", 0)
        generations_used = subscription.get("generations_used", 0)
        
        # Если лимит -1, то безлимитный план
        if generations_limit == -1:
            return True
        
        # Проверяем, есть ли доступные генерации
        return generations_used < generations_limit

    def use_generation(self, user_id):
        """
        Использование одной генерации (увеличение счетчика использованных генераций)
        
        Args:
            user_id (str): ID пользователя
            
        Returns:
            bool: True, если генерация успешно использована
        """
        user_id = str(user_id)
        
        if not self.can_generate_script(user_id):
            return False
        
        # Получаем данные подписки
        subscription = self.subscriptions["users"].get(user_id)
        if not subscription:
            return False
        
        # Увеличиваем счетчик использованных генераций
        subscription["generations_used"] = subscription.get("generations_used", 0) + 1
        
        # Сохраняем данные
        self._save_subscriptions()
        
        logger.info(f"Использована генерация для пользователя {user_id}. "
                   f"Использовано: {subscription['generations_used']}/{subscription.get('generations_limit', 0)}")
        
        return True

    def get_generations_info(self, user_id):
        """
        Получение информации о генерациях пользователя
        
        Args:
            user_id (str): ID пользователя
            
        Returns:
            dict: Информация о генерациях
        """
        user_id = str(user_id)
        
        if not self.has_active_subscription(user_id):
            return {"has_subscription": False}
        
        subscription = self.subscriptions["users"].get(user_id)
        if not subscription:
            return {"has_subscription": False}
        
        generations_limit = subscription.get("generations_limit", 0)
        generations_used = subscription.get("generations_used", 0)
        generations_left = max(0, generations_limit - generations_used) if generations_limit != -1 else -1
        
        return {
            "has_subscription": True,
            "generations_limit": generations_limit,
            "generations_used": generations_used,
            "generations_left": generations_left,
            "is_unlimited": generations_limit == -1,
            "can_generate": self.can_generate_script(user_id)
        }

# Создаем глобальный экземпляр менеджера подписок
subscription_manager = SubscriptionManager()

def check_user_subscription(user_id):
    """
    Функция для проверки подписки пользователя из других модулей
    
    Args:
        user_id (str): ID пользователя
        
    Returns:
        bool: True, если у пользователя есть активная подписка
    """
    # Debug logging
    original_user_id = user_id
    user_id = str(user_id)  # Ensure user_id is a string
    
    # Check if subscription exists in data
    has_subscription = "users" in subscription_manager.subscriptions and user_id in subscription_manager.subscriptions["users"]
    subscription_data = subscription_manager.subscriptions.get("users", {}).get(user_id, {})
    
    logger.info(f"[DEBUG] Checking subscription for user_id: {original_user_id} (converted to {user_id})")
    logger.info(f"[DEBUG] User exists in subscriptions data: {has_subscription}")
    logger.info(f"[DEBUG] Subscription data: {subscription_data}")
    
    # Check cache status
    cache_status = user_id in subscription_manager.active_cache
    cache_value = subscription_manager.active_cache.get(user_id, "Not in cache")
    logger.info(f"[DEBUG] User in active cache: {cache_status}, cache value: {cache_value}")
    
    # Get result
    result = subscription_manager.has_active_subscription(user_id)
    logger.info(f"[DEBUG] Final subscription check result: {result}")
    
    return result

def add_user_subscription(user_id, plan_name="Стандарт", duration_days=30, payment_id=None, generations_limit=None):
    """
    Функция для добавления подписки пользователя из других модулей
    
    Args:
        user_id (str): ID пользователя
        plan_name (str): Название плана подписки
        duration_days (int): Продолжительность подписки в днях
        payment_id (str): ID платежа в системе оплаты
        generations_limit (int): Лимит генераций для подписки
        
    Returns:
        bool: True, если подписка успешно добавлена
    """
    return subscription_manager.add_subscription(user_id, plan_name, duration_days, payment_id, generations_limit)

def get_subscription_info(user_id):
    """
    Функция для получения информации о подписке из других модулей
    
    Args:
        user_id (str): ID пользователя
        
    Returns:
        dict: Информация о подписке или None, если подписки нет
    """
    return subscription_manager.get_subscription_details(user_id)

def can_user_generate_script(user_id):
    """
    Проверка возможности создания скрипта пользователем
    
    Args:
        user_id (str): ID пользователя
        
    Returns:
        bool: True, если пользователь может создать скрипт
    """
    return subscription_manager.can_generate_script(user_id)

def use_user_generation(user_id):
    """
    Использование одной генерации пользователем
    
    Args:
        user_id (str): ID пользователя
        
    Returns:
        bool: True, если генерация успешно использована
    """
    return subscription_manager.use_generation(user_id)

def get_user_generations_info(user_id):
    """
    Получение информации о генерациях пользователя
    
    Args:
        user_id (str): ID пользователя
        
    Returns:
        dict: Информация о генерациях
    """
    return subscription_manager.get_generations_info(user_id)

# Для тестирования
if __name__ == "__main__":
    # Добавляем тестовую подписку
    add_user_subscription("123456", "Тестовый план", 30, "test_payment_id")
    
    # Проверяем статус подписки
    print(f"Статус подписки для пользователя 123456: {check_user_subscription('123456')}")
    
    # Получаем детали подписки
    print(f"Детали подписки для пользователя 123456: {get_subscription_info('123456')}") 