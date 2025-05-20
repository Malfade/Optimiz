// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;

// Basic app settings
const CONFIG = {
    apiUrl: window.location.origin,
    userId: null,
    userName: null
};

// Subscription plans
const PLANS = [
    { id: 'basic', name: 'Basic', price: 20, description: 'Access to basic features for 1 month' },
    { id: 'standard', name: 'Standard', price: 499, description: 'Access to all features for 1 month' },
    { id: 'premium', name: 'Premium', price: 999, description: 'Access to all features for 3 months with discount' }
];

// Global variables for payment tracking
let currentOrderId = null;
let paymentCheckActive = false;

// Initialize app when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Open Telegram WebApp
    tg.expand();
    tg.ready();

    // Get user data
    initUserData();

    // Initialize UI
    initUI();
    initEventListeners();
    
    // Check URL for payment status
    checkUrlForPaymentStatus();

    console.log('Telegram WebApp initialized', CONFIG.userId);
});

// Initialize user data
function initUserData() {
    // Try to get data from Telegram WebApp
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        CONFIG.userId = tg.initDataUnsafe.user.id;
        CONFIG.userName = tg.initDataUnsafe.user.first_name;
        console.log('User data received from Telegram:', CONFIG.userId, CONFIG.userName);
    } else {
        // Try to get from URL parameters
        CONFIG.userId = getQueryParam('userId');
        CONFIG.userName = getQueryParam('userName');
        console.log('User data received from URL:', CONFIG.userId, CONFIG.userName);
    }

    // If still no userId, create anonymous identifier
    if (!CONFIG.userId) {
        CONFIG.userId = `anonymous_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        console.log('Anonymous user ID created:', CONFIG.userId);
    }

    // If no username, use default
    if (!CONFIG.userName) {
        CONFIG.userName = 'User';
    }
}

// Check URL for YooKassa return parameters
function checkUrlForPaymentStatus() {
    const orderId = getQueryParam('order_id') || getQueryParam('orderId');
    const success = getQueryParam('success');
    const paymentId = getQueryParam('payment_id');
    
    console.log('Checking URL for payment status:', { orderId, success, paymentId });
    
    if (orderId && (success === 'true' || success === '1' || paymentId)) {
        console.log('Successful payment detected in URL:', orderId);
        handleSuccessfulPayment(orderId);
    }
}

// Initialize main interface
function initUI() {
    // Get username
    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        userNameElement.innerText = CONFIG.userName;
    }

    // Generate subscription cards
    const plansContainer = document.getElementById('plans');
    if (plansContainer) {
        PLANS.forEach(plan => {
            const planCard = createPlanCard(plan);
            plansContainer.appendChild(planCard);
        });
    }

    // Hide success modal on load
    const successModal = document.getElementById('successModal');
    if (successModal) {
        successModal.classList.add('hidden');
    }

    // Hide errors on load
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.classList.add('hidden');
    }
}

// Add event listeners
function initEventListeners() {
    // Handler for closing success modal
    const closeSuccessBtn = document.getElementById('closeSuccess');
    if (closeSuccessBtn) {
        closeSuccessBtn.addEventListener('click', () => {
            document.getElementById('successModal').classList.add('hidden');
            // Close Telegram app after closing modal
            tg.close();
        });
    }
    
    // Add handler for payment check button
    const checkPaymentButton = document.getElementById('checkPaymentButton');
    if (checkPaymentButton) {
        checkPaymentButton.addEventListener('click', () => {
            console.log('Manual payment status check');
            // Get current orderId
            if (currentOrderId) {
                // Change button text for feedback
                checkPaymentButton.textContent = 'Checking payment status...';
                checkPaymentButton.disabled = true;
                
                // Try to check payment status
                forceCheckPaymentStatus(currentOrderId).then(isSuccess => {
                    if (!isSuccess) {
                        // If cannot confirm payment automatically, ask user
                        if (confirm('Could not automatically determine payment status. If you are sure the payment was successful, click OK to activate subscription.')) {
                            handleSuccessfulPayment(currentOrderId);
                        } else {
                            // Return button to original state
                            checkPaymentButton.textContent = 'I already paid but don\'t see confirmation';
                            checkPaymentButton.disabled = false;
                        }
                    }
                    // If isSuccess = true, handleSuccessfulPayment will already be called in forceCheckPaymentStatus
                });
            } else {
                alert('Could not determine current payment identifier.');
            }
        });
    }
}

// Create subscription plan card
function createPlanCard(plan) {
    const card = document.createElement('div');
    card.className = 'plan-card';
    card.innerHTML = `
        <h3>${plan.name}</h3>
        <p class="price">${plan.price} RUB</p>
        <p class="description">${plan.description}</p>
        <button class="plan-button" data-plan-id="${plan.id}">Select</button>
    `;
    
    // Add handler to plan selection button
    const button = card.querySelector('button');
    button.addEventListener('click', () => handlePlanSelection(plan));
    
    return card;
}

// Handle subscription plan selection
async function handlePlanSelection(plan) {
    try {
        console.log('Plan selected:', plan);
        
        // Block buttons to prevent double clicks
        setButtonsState(false);
        
        // Show loading indicator
        showLoader();
        
        // Create payment on server
        const paymentResponse = await createPayment(plan.price, plan.id, CONFIG.userId);
        
        if (!paymentResponse || !paymentResponse.confirmation_token) {
            throw new Error('Could not get payment token');
        }
        
        console.log('Payment created:', paymentResponse);
        
        // Save payment ID for subsequent checks
        currentOrderId = paymentResponse.order_id || paymentResponse.id;
        
        // Prepare URL for return after payment
        const returnUrl = window.location.origin + window.location.pathname + 
                         `?order_id=${currentOrderId}&success=true&user_id=${CONFIG.userId}`;
                         
        console.log('Return URL after payment:', returnUrl);
        
        // Initialize payment widget or redirect
        if (paymentResponse.confirmation_token) {
            await initPaymentWidget(paymentResponse.confirmation_token, currentOrderId);
        } else if (paymentResponse.confirmation_url) {
            // Redirect to payment page
            window.location.href = paymentResponse.confirmation_url;
        } else {
            throw new Error('Could not get payment URL');
        }
        
    } catch (error) {
        console.error('Error creating payment:', error);
        showError(`Payment creation error: ${error.message}`);
        
        // Unblock buttons
        setButtonsState(true);
        
        // Hide loading indicator
        hideLoader();
    }
}

// Create payment on server
async function createPayment(amount, planName, userId) {
    try {
        console.log('Creating payment:', { amount, planName, userId });
        
        // Form URL for payment API
        const paymentUrl = `${CONFIG.apiUrl}/api/create-payment`;
        
        // Send request to create payment
        const response = await fetch(paymentUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                amount: amount,
                plan: planName,
                userId: userId,
                description: `Subscription ${planName} for user ${userId}`,
                return_url: window.location.href
            })
        });
        
        // Check request success
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Error creating payment');
        }
        
        // Parse response
        const paymentData = await response.json();
        return paymentData;
    } catch (error) {
        console.error('Error in payment creation request:', error);
        throw error;
    }
}

// Handle successful payment
function handleSuccessfulPayment(orderId) {
    console.log('Processing successful payment:', orderId);
    
    // Check if this payment has already been processed
    if (document.getElementById('successModal') && 
        !document.getElementById('successModal').classList.contains('hidden')) {
        console.log('Payment already processed, skipping duplicate notification');
        return;
    }
    
    // Use native Telegram popup instead of modal window
    if (tg.showPopup && typeof tg.showPopup === 'function') {
        // Show popup through Telegram Web App API
        tg.showPopup({
            title: 'Subscription activated!',
            message: 'Your subscription has been successfully activated. You can now use all bot features.',
            buttons: [
                { type: 'close' }
            ]
        }, function() {
            // After closing popup, close application
            tg.close();
        });
    } else {
        // Show success modal
        showSuccessModal();
    }
    
    // Send event to Telegram to activate subscription
    if (tg.sendData && typeof tg.sendData === 'function') {
        const responseData = {
            event: 'payment_success',
            order_id: orderId,
            user_id: CONFIG.userId
        };
        
        try {
            // Send successful payment data to bot
            tg.sendData(JSON.stringify(responseData));
            console.log('Successful payment data sent to bot:', responseData);
        } catch (error) {
            console.error('Error sending data to bot:', error);
        }
    } else {
        console.warn('tg.sendData not available. Cannot send data to bot.');
    }
}

// Force payment status check
async function forceCheckPaymentStatus(orderId) {
    try {
        console.log('Forced payment status check:', orderId);
        
        const statusUrl = `${CONFIG.apiUrl}/api/payment-status/${orderId}`;
        const response = await fetch(statusUrl);
        
        if (!response.ok) {
            throw new Error('Error checking payment status');
        }
        
        const data = await response.json();
        console.log('Payment status response received:', data);
        
        // Check payment status
        if (data.status === 'succeeded' || data.status === 'success') {
            console.log('Payment successful, calling handler');
            handleSuccessfulPayment(orderId);
            return true;
        } else {
            console.log('Payment not successful:', data.status);
            return false;
        }
    } catch (error) {
        console.error('Error checking payment status:', error);
        return false;
    }
}

// Show success modal
function showSuccessModal() {
    const successModal = document.getElementById('successModal');
    if (successModal) {
        successModal.classList.remove('hidden');
        tg.BackButton.show();
    }
}

// Show error message
function showError(message) {
    console.error('Error:', message);
    
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
        
        // Hide error message after 5 seconds
        setTimeout(() => {
            errorElement.classList.add('hidden');
        }, 5000);
    }
}

// Show loading indicator
function showLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.classList.remove('hidden');
    }
}

// Hide loading indicator
function hideLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.classList.add('hidden');
    }
}

// Manage button state
function setButtonsState(enabled) {
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.disabled = !enabled;
    });
}

// Get parameter from URL
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
} 