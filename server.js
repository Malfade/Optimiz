// Простой серверный скрипт для интеграции с ЮKassa
// Для запуска: node server.js
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Настройка CORS для запросов с фронтенда
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname)));

// Для хранения заказов (в реальном приложении используйте базу данных)
const orders = {};

// Инициализация ЮKassa
// ВНИМАНИЕ: В реальном приложении эти данные должны храниться в безопасном месте (env переменные)
const shopId = '1086529'; // Ваш идентификатор магазина ЮKassa
const secretKey = 'test_fItob0t2XOZPQETIa7npqoKf5PsxbXlrMTHV88P4WZA'; // Тестовый ключ ЮKassa

// Режим работы (true - тестовый, false - боевой)
const isTestMode = true;

// Инициализация клиента ЮKassa
let yooKassa = null;
try {
    const YooKassa = require('yookassa');
    yooKassa = new YooKassa({
        shopId: shopId,
        secretKey: secretKey
    });
    console.log('ЮKassa клиент инициализирован в', isTestMode ? 'тестовом' : 'боевом', 'режиме');
} catch (error) {
    console.error('Ошибка инициализации ЮKassa:', error);
    console.error('Установите библиотеку командой: npm install yookassa --save');
}

// Маршрут для обслуживания HTML
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Маршрут для создания платежа
app.post('/api/create-payment', async (req, res) => {
    console.log('Получен запрос на создание платежа:', req.body);
    
    try {
        // Получаем данные из запроса
        const { amount, plan, userId, description, return_url, email } = req.body;
        
        // Проверяем обязательные параметры
        if (!amount || !userId) {
            return res.status(400).json({ 
                error: 'Отсутствуют обязательные параметры (amount, userId)' 
            });
        }
        
        // Безопасные значения для параметров
        const safeAmount = parseFloat(amount) || 100; // По умолчанию 100 рублей
        const planName = plan || 'Стандартный';
        const safeUserId = String(userId).replace(/[^a-zA-Z0-9_-]/g, '');
        const safeEmail = email || 'user@example.com';
        
        // Проверяем, инициализирован ли клиент ЮKassa
        if (!yooKassa) {
            return res.status(500).json({ 
                error: 'Сервер оплаты не настроен' 
            });
        }

        try {
            // Создаем заказ в ЮKassa
            let idempotenceKey = crypto.randomUUID ? 
                crypto.randomUUID() : 
                Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            
            console.log('Создаем платеж в ЮKassa с параметрами:', {
                amount: safeAmount, description, idempotenceKey, safeUserId, isTestMode, email: safeEmail
            });
            
            // Настраиваем параметры платежа
            const paymentParams = {
                amount: {
                    value: safeAmount,
                    currency: 'RUB'
                },
                capture: true, // Автоматически принимать поступившие средства
                description: description || `Подписка ${planName} для пользователя ${safeUserId}`,
                metadata: {
                    userId: safeUserId,
                    planName: planName
                }
            };

            // Добавляем параметр confirmation в зависимости от режима
            if (isTestMode) {
                // В тестовом режиме используем redirect для надежности
                paymentParams.confirmation = {
                    type: 'redirect',
                    return_url: return_url || `${req.protocol}://${req.get('host')}?success=true`
                };
            } else {
                // В боевом режиме используем embedded
                paymentParams.confirmation = {
                    type: 'embedded',
                    locale: 'ru_RU'
                };
                
                // Добавляем данные для чека (требуется по 54-ФЗ)
                paymentParams.receipt = {
                    customer: {
                        email: safeEmail // Используем email от пользователя
                    },
                    items: [
                        {
                            description: `Подписка "${planName}"`,
                            amount: {
                                value: safeAmount,
                                currency: "RUB"
                            },
                            vat_code: 1, // НДС 20%
                            quantity: 1,
                            payment_subject: "service",
                            payment_mode: "full_payment"
                        }
                    ]
                };
            }
            
            // Создаем платеж
            const payment = await yooKassa.createPayment(paymentParams, idempotenceKey);
            
            // Сохраняем информацию о заказе
            orders[payment.id] = {
                status: payment.status,
                userId: safeUserId,
                amount: safeAmount,
                planName: planName,
                createdAt: new Date(),
                email: safeEmail
            };
            
            console.log('Платеж успешно создан:', payment.id);
            console.log('Данные для оплаты:', payment.confirmation);
            
            // Подготавливаем ответ клиенту
            const response = {
                order_id: payment.id,
                status: payment.status,
                amount: safeAmount,
                testMode: isTestMode
            };

            // Добавляем конфирмацию в зависимости от типа
            if (isTestMode) {
                response.confirmation_url = payment.confirmation.confirmation_url;
            } else {
                response.confirmation_token = payment.confirmation.confirmation_token;
            }
            
            // Отправляем клиенту информацию о платеже
            return res.json(response);
        } catch (yooKassaError) {
            console.error('Ошибка при создании платежа в ЮKassa:', yooKassaError);
            return res.status(500).json({ 
                error: 'Ошибка при создании платежа', 
                details: String(yooKassaError)
            });
        }
    } catch (error) {
        console.error('Внутренняя ошибка сервера при создании платежа:', error);
        return res.status(500).json({ 
            error: 'Внутренняя ошибка сервера', 
            details: String(error)
        });
    }
});

// Маршрут для проверки статуса платежа
app.get('/api/payment-status/:orderId', async (req, res) => {
    const orderId = req.params.orderId;
    
    console.log(`Получен запрос на проверку статуса платежа: ${orderId}`);
    
    try {
        // Проверяем, есть ли информация о заказе в нашей "базе данных"
        if (orders[orderId]) {
            // Если заказ уже отмечен как успешный в нашей БД
            if (orders[orderId].status === 'succeeded') {
                return res.json({ 
                    status: 'succeeded', 
                    orderId: orderId
                });
            }
        }
        
        // Если заказ не найден или статус не succeeded, делаем запрос к ЮKassa
        if (yooKassa) {
            try {
                // Получаем информацию о платеже от ЮKassa
                const payment = await yooKassa.getPayment(orderId);
                
                // Обновляем статус в нашей "базе данных"
                if (orders[orderId]) {
                    orders[orderId].status = payment.status;
                } else {
                    // Если заказа нет в нашей БД, создаем запись
                    orders[orderId] = {
                        status: payment.status,
                        createdAt: new Date()
                    };
                }
                
                // Отправляем статус клиенту
                return res.json({
                    status: payment.status,
                    orderId: orderId
                });
            } catch (yooKassaError) {
                console.error(`Ошибка при получении информации о платеже ${orderId}:`, yooKassaError);
                return res.status(500).json({ 
                    error: 'Ошибка при получении информации о платеже', 
                    details: String(yooKassaError)
                });
            }
        } else {
            // Если клиент ЮKassa не инициализирован
            return res.status(500).json({ 
                error: 'Сервер оплаты не настроен' 
            });
        }
    } catch (error) {
        console.error(`Внутренняя ошибка сервера при проверке статуса платежа ${orderId}:`, error);
        return res.status(500).json({ 
            error: 'Внутренняя ошибка сервера', 
            details: String(error)
        });
    }
});

// Маршрут для webhook от ЮKassa
app.post('/api/webhook', async (req, res) => {
    // Ключ из уведомления
    const requestBody = req.body;
    
    try {
        console.log('Получено webhook-уведомление:', JSON.stringify(requestBody));
        
        const event = requestBody.event;
        const paymentId = requestBody.object?.id;
        
        if (!event || !paymentId) {
            console.error('Некорректные данные в webhook-уведомлении');
            return res.status(400).json({ error: 'Некорректные данные' });
        }
        
        console.log(`Получено уведомление: ${event} для платежа ${paymentId}`);
        
        if (event === 'payment.succeeded') {
            // Платеж успешно завершен
            if (orders[paymentId]) {
                orders[paymentId].status = 'succeeded';
                
                // В реальном приложении здесь нужно обновить информацию в базе данных
                // И отправить уведомление пользователю через бота
                console.log(`Платеж ${paymentId} успешно завершен`);
            } else {
                console.log(`Платеж ${paymentId} не найден в локальной базе, но успешно завершен`);
                // Создаем запись, если ее нет
                orders[paymentId] = {
                    status: 'succeeded',
                    createdAt: new Date()
                };
            }
            
            // Отправка запроса на webhook Flask для активации подписки
            try {
                const userId = orders[paymentId]?.userId;
                const planName = orders[paymentId]?.planName || 'standard';
                
                if (userId) {
                    // Здесь можно отправить запрос на webhook сервера Flask для активации подписки
                    const webhookUrl = 'http://localhost:5000/webhook/payment';
                    console.log(`Отправка уведомления на webhook: ${webhookUrl}, userId: ${userId}, plan: ${planName}`);
                }
            } catch (webhookError) {
                console.error('Ошибка при отправке уведомления на webhook:', webhookError);
            }
        } else if (event === 'payment.canceled') {
            // Платеж отменен
            if (orders[paymentId]) {
                orders[paymentId].status = 'canceled';
                console.log(`Платеж ${paymentId} отменен`);
            } else {
                console.log(`Платеж ${paymentId} не найден в локальной базе, но отменен`);
            }
        }
        
        // Отвечаем сервису ЮKassa, что уведомление обработано
        res.sendStatus(200);
    } catch (error) {
        console.error('Ошибка при обработке webhook:', error);
        res.status(500).json({ error: 'Ошибка при обработке webhook' });
    }
});

// Маршрут для отладки - сброс хранилища заказов
app.get('/api/debug/reset-orders', (req, res) => {
    console.log('Сброс хранилища заказов');
    Object.keys(orders).forEach(key => delete orders[key]);
    res.json({ message: 'Хранилище заказов очищено', ordersCount: Object.keys(orders).length });
});

// Маршрут для получения всех заказов (только для отладки!)
app.get('/api/debug/orders', (req, res) => {
    console.log('Запрос всех заказов (debug)');
    res.json({ orders: orders, count: Object.keys(orders).length });
});

// Запуск сервера
app.listen(PORT, () => {
    console.log(`Сервер монетизации запущен на порту ${PORT}`);
    console.log(`Основной URL: http://localhost:${PORT}`);
}); 