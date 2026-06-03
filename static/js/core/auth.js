/**
 * Auth Pages Logic
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Initialize particles
    if (typeof initParticles === 'function') {
        initParticles();
    }
    
    // Custom form validation
    initFormValidation();
});

/**
 * Initialize custom form validation
 */
function initFormValidation() {
    const form = document.querySelector('.auth-form');
    if (!form) return;
    
    const inputs = form.querySelectorAll('.form-input');
    
    // Validation messages in Russian
    const validationMessages = {
        username: 'Введите имя пользователя',
        email: 'Введите корректный email',
        password: 'Введите пароль',
        password1: 'Введите пароль',
        password2: 'Пароли не совпадают',
        required: 'Это поле обязательно'
    };
    
    inputs.forEach(input => {
        // Create validation message element
        const wrapper = input.closest('.form-group');
        if (wrapper) {
            const messageEl = document.createElement('div');
            messageEl.className = 'validation-message hidden';
            messageEl.innerHTML = '<i data-lucide="alert-circle"></i><span class="message-text"></span>';
            wrapper.appendChild(messageEl);
        }
        
        // Validate on blur
        input.addEventListener('blur', function() {
            validateInput(input, validationMessages);
        });
        
        // Clear validation on input
        input.addEventListener('input', function() {
            clearValidation(input);
        });
    });
    
    // Form submit validation
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        inputs.forEach(input => {
            if (!validateInput(input, validationMessages)) {
                isValid = false;
            }
        });
        
        // Check password confirmation
        const password1 = form.querySelector('#id_password1');
        const password2 = form.querySelector('#id_password2');
        
        if (password1 && password2 && password1.value !== password2.value) {
            const wrapper = password2.closest('.form-group');
            const messageEl = wrapper?.querySelector('.validation-message');
            if (messageEl) {
                messageEl.classList.remove('hidden');
                messageEl.querySelector('.message-text').textContent = validationMessages.password2;
                password2.classList.add('invalid');
            }
            isValid = false;
        }
        
        if (!isValid) {
            e.preventDefault();
            // Re-initialize icons for new elements
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
    });
}

/**
 * Validate single input
 */
function validateInput(input, messages) {
    const wrapper = input.closest('.form-group');
    const messageEl = wrapper?.querySelector('.validation-message');
    
    if (!input.validity.valid) {
        input.classList.add('invalid');
        
        if (messageEl) {
            messageEl.classList.remove('hidden');
            const messageText = messageEl.querySelector('.message-text');
            
            if (input.validity.valueMissing) {
                messageText.textContent = messages[input.name] || messages.required;
            } else if (input.validity.typeMismatch) {
                messageText.textContent = messages[input.name] || 'Неверный формат';
            } else {
                messageText.textContent = input.validationMessage;
            }
        }
        
        return false;
    }
    
    input.classList.remove('invalid');
    if (messageEl) {
        messageEl.classList.add('hidden');
    }
    
    return true;
}

/**
 * Clear validation state
 */
function clearValidation(input) {
    const wrapper = input.closest('.form-group');
    const messageEl = wrapper?.querySelector('.validation-message');
    
    input.classList.remove('invalid');
    if (messageEl) {
        messageEl.classList.add('hidden');
    }
}