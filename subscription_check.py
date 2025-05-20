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
MONETIZATION_SERVER_URL = "http://localhost:3001"  # В реальном окружении замените на актуальный URL

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
        
        for user_id, subscription in self.subscriptions.get("users", {}).items():
            # Проверяем, что подписка активна (оплачена и не истекла)
            if subscription.get("status") == "active" and subscription.get("expires_at", 0) > current_time:
                self.active_cache[user_id] = True
            else:
                self.active_cache[user_id] = False
    
    def add_subscription(self, user_id, plan_name, duration_days=30, payment_id=None):
        """
        Добавление новой подписки для пользователя
        
        Args:
            user_id (str): ID пользователя
            plan_name (str): Название плана подписки
            duration_days (int): Продолжительность подписки в днях
            payment_id (str): ID платежа в системе оплаты
            
        Returns:
            bool: True, если подписка успешно добавлена
        """
        try:
            # Создаем записи в структуре, если их еще нет
            if "users" not in self.subscriptions:
                self.subscriptions["users"] = {}
                
            # Получаем текущее время
            now = datetime.now()
            
            # Вычисляем дату окончания подписки
            expires_at = (now + timedelta(days=duration_days)).timestamp()
            
            # Добавляем информацию о подписке
            self.subscriptions["users"][str(user_id)] = {
                "plan_name": plan_name,
                "status": "active",
                "created_at": now.timestamp(),
                "expires_at": expires_at,
                "payment_id": payment_id
            }
            
            # Сохраняем данные и обновляем кеш
            self._save_subscriptions()
            
            logger.info(f"Добавлена подписка для пользователя {user_id}, план {plan_name}, " 
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
        user_id = str(user_id)
        
        # Сначала проверяем кеш для быстрого ответа
        if user_id in self.active_cache:
            return self.active_cache[user_id]
        
        # Если пользователя нет в кеше, проверяем полностью
        if "users" not in self.subscriptions or user_id not in self.subscriptions["users"]:
            return False
        
        subscription = self.subscriptions["users"][user_id]
        
        # Проверяем статус и срок действия подписки
        if subscription.get("status") != "active":
            return False
        
        current_time = datetime.now().timestamp()
        if subscription.get("expires_at", 0) <= current_time:
            # Подписка истекла, обновляем ее статус
            subscription["status"] = "expired"
            self._save_subscriptions()
            return False
        
        return True
    
    def check_payment_status(self, payment_id):
        """
        Проверка статуса платежа через API сервера монетизации
        
        Args:
            payment_id (str): ID платежа
            
        Returns:
            bool: True, если платеж успешно завершен
        """
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
            
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса платежа {payment_id}: {e}")
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
    return subscription_manager.has_active_subscription(user_id)

def add_user_subscription(user_id, plan_name="Стандарт", duration_days=30, payment_id=None):
    """
    Функция для добавления подписки пользователя из других модулей
    
    Args:
        user_id (str): ID пользователя
        plan_name (str): Название плана подписки
        duration_days (int): Продолжительность подписки в днях
        payment_id (str): ID платежа в системе оплаты
        
    Returns:
        bool: True, если подписка успешно добавлена
    """
    return subscription_manager.add_subscription(user_id, plan_name, duration_days, payment_id)

def get_subscription_info(user_id):
    """
    Функция для получения информации о подписке из других модулей
    
    Args:
        user_id (str): ID пользователя
        
    Returns:
        dict: Информация о подписке или None, если подписки нет
    """
    return subscription_manager.get_subscription_details(user_id)

# Для тестирования
if __name__ == "__main__":
    # Добавляем тестовую подписку
    add_user_subscription("123456", "Тестовый план", 30, "test_payment_id")
    
    # Проверяем статус подписки
    print(f"Статус подписки для пользователя 123456: {check_user_subscription('123456')}")
    
    # Получаем детали подписки
    print(f"Детали подписки для пользователя 123456: {get_subscription_info('123456')}") 