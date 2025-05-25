// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;

// Основные настройки приложения
const CONFIG = {
    apiUrl: window.location.origin, // Используем тот же домен что и бот
    userId: null,
    userName: null,
    isDev: false
};

// Подписки и их цены
const PLANS = [
    { id: 'basic', name: 'Базовый', price: 20, description: 'Доступ к основным функциям бота на 1 месяц' },
    { id: 'standard', name: 'Стандартный', price: 499, description: 'Доступ ко всем функциям бота на 1 месяц' },
    { id: 'premium', name: 'Премиум', price: 999, description: 'Доступ ко всем функциям бота на 3 месяца со скидкой' }
];

// Глобальные переменные для отслеживания платежа
let currentOrderId = null;
let paymentCheckActive = false;

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Открываем Telegram WebApp
    tg.expand();
    tg.ready();

    // Получаем данные пользователя
    initUserData();

    // Инициализируем интерфейс
    initUI();
    initEventListeners();
    
    // Проверяем параметры URL для определения статуса платежа
    checkUrlForPaymentStatus();

    console.log('Telegram WebApp initialized', CONFIG.userId);
});

// Инициализация данных пользователя
function initUserData() {
    // Проверяем startapp параметр для получения user_id от бота
    const startApp = tg.initDataUnsafe?.start_param || '';
    let userIdFromBot = null;
    
    if (startApp && startApp.startsWith('user_id_')) {
        userIdFromBot = startApp.replace('user_id_', '');
        console.log('Получен user_id из start_param:', userIdFromBot);
    }
    
    // Также проверяем URL параметры
    const urlParams = new URLSearchParams(window.location.search);
    const userIdFromUrl = urlParams.get('user_id') || urlParams.get('userId');
    
    // Пытаемся получить данные из Telegram WebApp
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        CONFIG.userId = userIdFromBot || userIdFromUrl || tg.initDataUnsafe.user.id;
        CONFIG.userName = tg.initDataUnsafe.user.first_name;
        console.log('Получены данные пользователя из Telegram:', CONFIG.userId, CONFIG.userName);
    } else {
        CONFIG.userId = userIdFromBot || userIdFromUrl;
        CONFIG.userName = urlParams.get('userName') || urlParams.get('user_name');
        console.log('Получены данные пользователя из URL/start_param:', CONFIG.userId, CONFIG.userName);
    }

    // Если всё еще нет userId, создаем анонимный идентификатор
    if (!CONFIG.userId) {
        CONFIG.userId = `anonymous_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        console.log('Создан анонимный идентификатор пользователя:', CONFIG.userId);
    }

    if (!CONFIG.userName) {
        CONFIG.userName = 'Пользователь';
    }

    console.log('Финальные данные пользователя:', {
        userId: CONFIG.userId,
        userName: CONFIG.userName
    });
}

// Проверка URL на наличие параметров возврата от YooKassa
function checkUrlForPaymentStatus() {
    const orderId = getQueryParam('order_id') || getQueryParam('orderId');
    const success = getQueryParam('success');
    const paymentId = getQueryParam('payment_id');
    
    console.log('Проверка URL на статус платежа:', { orderId, success, paymentId });
    
    if (orderId && (success === 'true' || success === '1' || paymentId)) {
        console.log('Обнаружен успешный платеж в URL:', orderId);
        handleSuccessfulPayment(orderId);
    }
}

// Инициализация основного интерфейса
function initUI() {
    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        userNameElement.innerText = CONFIG.userName;
    }

    // Генерируем карточки подписок
    const plansContainer = document.getElementById('plans');
    if (plansContainer) {
        PLANS.forEach((plan, index) => {
            const planCard = createPlanCard(plan, index === 1); // Стандартный план рекомендуемый
            plansContainer.appendChild(planCard);
        });
    }

    // Скрываем модальные окна при загрузке
    const successModal = document.getElementById('successModal');
    if (successModal) {
        successModal.classList.add('hidden');
    }

    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.classList.add('hidden');
    }
}

// Создание карточки тарифного плана
function createPlanCard(plan, isRecommended = false) {
    const card = document.createElement('div');
    card.className = `plan-card ${isRecommended ? 'recommended' : ''}`;
    card.id = `plan-${plan.id}`;

    card.innerHTML = `
        <h3>${plan.name}</h3>
        <p class="price">${plan.price} ₽</p>
        <p class="description">${plan.description}</p>
        <button class="buy-btn" data-plan-id="${plan.id}" data-plan-name="${plan.name}" data-price="${plan.price}">
            Оформить
        </button>
    `;

    // Добавляем обработчик нажатия на кнопку "Оформить"
    const buyBtn = card.querySelector('.buy-btn');
    buyBtn.addEventListener('click', () => handlePlanSelection(plan));

    return card;
}

// Добавляем обработчики событий
function initEventListeners() {
    // Обработчик для закрытия модального окна успешной оплаты
    const closeSuccessBtn = document.getElementById('closeSuccess');
    if (closeSuccessBtn) {
        closeSuccessBtn.addEventListener('click', () => {
            document.getElementById('successModal').classList.add('hidden');
            tg.close();
        });
    }
    
    // Добавляем обработчик для кнопки проверки платежа
    const checkPaymentButton = document.getElementById('checkPaymentButton');
    if (checkPaymentButton) {
        checkPaymentButton.addEventListener('click', () => {
            console.log('Ручная проверка статуса платежа');
            if (currentOrderId) {
                checkPaymentButton.textContent = 'Проверяем статус платежа...';
                checkPaymentButton.disabled = true;
                
                forceCheckPaymentStatus(currentOrderId).then(isSuccess => {
                    if (!isSuccess) {
                        if (confirm('Не удалось автоматически определить статус платежа. Если вы уверены, что оплата прошла успешно, нажмите OK для активации подписки.')) {
                            handleSuccessfulPayment(currentOrderId);
                        } else {
                            checkPaymentButton.textContent = 'Я уже оплатил, но не вижу подтверждения';
                            checkPaymentButton.disabled = false;
                        }
                    }
                });
            } else {
                alert('Не удалось определить идентификатор текущего платежа.');
            }
        });
    }

    // Добавляем обработчик для кнопки Назад в мини-приложении
    tg.BackButton.onClick(() => {
        const paymentModal = document.getElementById('paymentModal');
        if (paymentModal && !paymentModal.classList.contains('hidden')) {
            paymentModal.classList.add('hidden');
            tg.BackButton.hide();
            return;
        }
        
        const successModal = document.getElementById('successModal');
        if (successModal && !successModal.classList.contains('hidden')) {
            successModal.classList.add('hidden');
            tg.close();
            return;
        }
    });
}

// Обработка выбора тарифного плана
async function handlePlanSelection(plan) {
    console.log(`Выбран план "${plan.name}" за ${plan.price} ₽`);
    
    window.selectedPlan = plan;
    
    showLoader();
    setButtonsState(false);
    
    try {
        if (!CONFIG.userId) {
            initUserData();
        }
        
        console.log('Отправляем запрос на создание платежа с пользователем:', CONFIG.userId);
        
        const paymentData = await createPayment(plan.price, plan.name, CONFIG.userId, plan);
        console.log('Данные платежа:', paymentData);
        
        if (!paymentData || paymentData.error) {
            throw new Error(paymentData?.error || 'Не удалось создать платеж');
        }
        
        currentOrderId = paymentData.orderId;
        
        if (paymentData.testMode && paymentData.redirectUrl) {
            console.log('Перенаправляем на страницу оплаты:', paymentData.redirectUrl);
            window.location.href = paymentData.redirectUrl;
        } else {
            await initPaymentWidget(paymentData.confirmationToken, paymentData.orderId);
            
            if (tg.BackButton) {
                tg.BackButton.show();
            }
        }
    } catch (error) {
        console.error('Ошибка при создании платежа:', error);
        showError(`Не удалось создать платеж: ${error.message}`);
    } finally {
        hideLoader();
        setButtonsState(true);
    }
}

// Функция для создания платежа на сервере
async function createPayment(amount, planName, userId, plan) {
    try {
        console.log(`Создание платежа: ${amount} руб., план: ${planName}, пользователь: ${userId}`);
        
        let email = "customer@example.com";
        
        try {
            const userEmail = prompt("Введите email для получения чека:", "");
            if (userEmail && userEmail.includes("@") && userEmail.includes(".")) {
                email = userEmail;
            }
        } catch (e) {
            console.log("Не удалось запросить email, используем значение по умолчанию");
        }
        
        const response = await fetch(`${CONFIG.apiUrl}/api/create-payment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                amount: amount.toString(),
                planName: planName,
                userId: userId,
                description: `Подписка "${planName}"`,
                email: email,
                plan: plan
            })
        });
        
        const responseData = await response.json();
        
        if (!response.ok) {
            throw new Error(responseData.error || responseData.details || `Ошибка сервера: ${response.status}`);
        }
        
        return responseData;
    } catch (error) {
        console.error('Ошибка при создании платежа:', error);
        throw error;
    }
}

// Функция для обработки успешного платежа
async function handleSuccessfulPayment(orderId) {
    try {
        console.log(`Обработка успешного платежа: ${orderId}`);
        
        stopPaymentChecks();
        
        const paymentModal = document.getElementById('paymentModal');
        if (paymentModal) {
            paymentModal.classList.add('hidden');
        }
        
        hideLoader();
        
        let planName = 'Стандарт';
        let planDuration = 30;
        
        if (window.selectedPlan) {
            planName = window.selectedPlan.name;
            if (window.selectedPlan.id === 'basic') {
                planDuration = 30;
            } else if (window.selectedPlan.id === 'premium') {
                planDuration = 90;
            } else {
                planDuration = 30;
            }
        }
        
        const subscriptionResponse = await fetch(`${CONFIG.apiUrl}/api/activate-subscription`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userId: CONFIG.userId,
                orderId: orderId,
                planName: planName,
                planDuration: planDuration
            })
        });
        
        const subscriptionData = await subscriptionResponse.json();
        
        if (!subscriptionResponse.ok || !subscriptionData.success) {
            throw new Error(subscriptionData.error || 'Не удалось активировать подписку');
        }
        
        console.log('Подписка успешно активирована:', subscriptionData);
        
        if (tg.showPopup && typeof tg.showPopup === 'function') {
            tg.showPopup({
                title: '✅ Оплата успешна!',
                message: `Ваша подписка "${planName}" успешно активирована на ${planDuration} дней`,
                buttons: [{ type: 'close' }]
            }, () => {
                tg.close();
            });
        } else {
            const successModal = document.getElementById('successModal');
            if (successModal) {
                const modalTitle = successModal.querySelector('h2');
                const modalText = successModal.querySelector('p');
                if (modalTitle) modalTitle.textContent = 'Оплата успешна!';
                if (modalText) modalText.textContent = `Ваша подписка "${planName}" активирована на ${planDuration} дней`;
                
                successModal.classList.remove('hidden');
                successModal.classList.add('modal-visible');
            }
            
            setTimeout(() => {
                tg.close();
            }, 3000);
        }
        
    } catch (error) {
        console.error('Ошибка при обработке успешного платежа:', error);
        
        if (tg.showAlert && typeof tg.showAlert === 'function') {
            tg.showAlert(`Ошибка при активации подписки: ${error.message}`);
        } else {
            showError(`Ошибка при активации подписки: ${error.message}`);
        }
    }
}

// Остановка всех проверок статуса платежа
function stopPaymentChecks() {
    if (window.statusCheckInterval) {
        clearInterval(window.statusCheckInterval);
        window.statusCheckInterval = null;
    }
    paymentCheckActive = false;
}

// Инициализация платежного виджета ЮKassa
async function initPaymentWidget(token, orderId) {
    console.log('Инициализация платежного виджета YooKassa');
    
    const paymentContainer = document.getElementById('paymentFormContainer');
    paymentContainer.innerHTML = '';
    
    const paymentModal = document.getElementById('paymentModal');
    paymentModal.classList.remove('hidden');
    
    const closePaymentBtn = document.getElementById('closePayment');
    closePaymentBtn.addEventListener('click', () => {
        paymentModal.classList.add('hidden');
        stopPaymentChecks();
        if (tg.BackButton) {
            tg.BackButton.hide();
        }
    });
    
    try {
        if (typeof YooMoneyCheckoutWidget !== 'function') {
            throw new Error('Библиотека YooKassa не загружена');
        }
        
        const yooKassaWidget = new YooMoneyCheckoutWidget({
            confirmation_token: token,
            return_url: window.location.href + '?orderId=' + orderId + '&success=true',
            embedded_3ds: true,
            error_callback: function(error) {
                console.error('Ошибка YooKassa виджета:', error);
                showError(`Ошибка платежного виджета: ${error.message || 'Неизвестная ошибка'}`);
            },
            success_callback: function(data) {
                console.log('Успешная оплата YooKassa:', data);
                handleSuccessfulPayment(orderId);
            }
        });
        
        yooKassaWidget.render('paymentFormContainer')
            .then(() => {
                console.log('Виджет YooKassa успешно отрисован');
                checkPaymentStatus(orderId);
                setupAdditionalPaymentChecks(orderId);
            })
            .catch(err => {
                console.error('Ошибка при отрисовке виджета YooKassa:', err);
                showError(`Не удалось отобразить форму оплаты: ${err.message || 'Неизвестная ошибка'}`);
            });
    } catch (error) {
        console.error('Ошибка инициализации виджета YooKassa:', error);
        showError(`Ошибка инициализации платежного виджета: ${error.message}`);
    }
}

// Функция для проверки статуса платежа
function checkPaymentStatus(orderId) {
    console.log(`Начинаем проверку статуса платежа ${orderId}`);
    
    if (paymentCheckActive) {
        console.log('Проверка статуса уже активна, пропускаем');
        return;
    }
    
    paymentCheckActive = true;
    stopPaymentChecks();
    
    window.statusCheckInterval = setInterval(async () => {
        try {
            const paymentModal = document.getElementById('paymentModal');
            if (paymentModal && paymentModal.classList.contains('hidden')) {
                console.log('Модальное окно платежа закрыто, останавливаем проверку статуса');
                stopPaymentChecks();
                return;
            }
            
            const response = await fetch(`${CONFIG.apiUrl}/api/payment-status/${orderId}`);
            
            if (!response.ok) {
                console.error('Ошибка при запросе статуса платежа:', response.status);
                return;
            }
            
            const statusData = await response.json();
            console.log(`Статус платежа ${orderId}:`, statusData);
            
            if (statusData.status === 'succeeded') {
                stopPaymentChecks();
                handleSuccessfulPayment(orderId);
            }
            
            if (statusData.status === 'canceled') {
                stopPaymentChecks();
                showError('Платеж был отменен');
            }
        } catch (error) {
            console.error('Ошибка при проверке статуса платежа:', error);
        }
    }, 2000);
    
    setTimeout(() => {
        if (paymentCheckActive) {
            stopPaymentChecks();
            console.log(`Проверка статуса платежа ${orderId} остановлена по таймауту`);
            
            const paymentModal = document.getElementById('paymentModal');
            if (paymentModal && !paymentModal.classList.contains('hidden')) {
                if (confirm('Не удалось получить подтверждение платежа. Если вы уже оплатили, нажмите OK, чтобы подтвердить оплату.')) {
                    handleSuccessfulPayment(orderId);
                }
            }
        }
    }, 180000);
}

// Установка дополнительных проверок статуса платежа
function setupAdditionalPaymentChecks(orderId) {
    const checkPoints = [15000, 30000, 60000];
    
    checkPoints.forEach(delay => {
        setTimeout(() => {
            const paymentModal = document.getElementById('paymentModal');
            const successModal = document.getElementById('successModal');
            
            if (paymentModal && 
                !paymentModal.classList.contains('hidden') && 
                successModal && 
                successModal.classList.contains('hidden')) {
                console.log(`Проверка статуса платежа ${orderId} по таймеру ${delay}ms`);
                forceCheckPaymentStatus(orderId);
            }
        }, delay);
    });
}

// Принудительная проверка статуса платежа
async function forceCheckPaymentStatus(orderId) {
    try {
        console.log(`Принудительная проверка статуса платежа: ${orderId}`);
        
        const response = await fetch(`${CONFIG.apiUrl}/api/payment-status/${orderId}`);
        
        if (!response.ok) {
            console.error('Ошибка при запросе статуса платежа:', response.status);
            return false;
        }
        
        const statusData = await response.json();
        console.log(`Получен статус платежа ${orderId}:`, statusData);
        
        if (statusData.status === 'succeeded') {
            console.log('Обнаружен успешный платеж при принудительной проверке');
            handleSuccessfulPayment(orderId);
            return true;
        }
    } catch (error) {
        console.error('Ошибка при принудительной проверке статуса платежа:', error);
    }
    
    return false;
}

// Показать сообщение об ошибке
function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
        
        setTimeout(() => {
            errorElement.classList.add('hidden');
        }, 5000);
    } else {
        alert(message);
    }
}

// Показать индикатор загрузки
function showLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.classList.remove('hidden');
    }
}

// Скрыть индикатор загрузки
function hideLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.classList.add('hidden');
    }
}

// Включить/отключить кнопки покупки
function setButtonsState(enabled) {
    const buttons = document.querySelectorAll('.buy-btn');
    buttons.forEach(button => {
        button.disabled = !enabled;
    });
}

// Вспомогательная функция для получения параметров из URL
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
} 