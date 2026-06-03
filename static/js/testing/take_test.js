/**
 * Take Test Page Logic
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
    
    // Initialize timer
    initTimer();
    
    // Initialize submit modal
    initSubmitModal();
});

/**
 * Initialize countdown timer
 */
function initTimer() {
    const timerEl = document.getElementById('timer');
    if (!timerEl) return;
    
    const endsAtIso = timerEl.getAttribute('data-ends-at');
    if (!endsAtIso) return;
    
    const endsAt = new Date(endsAtIso).getTime();
    
    function updateTimer() {
        const now = new Date().getTime();
        const distance = endsAt - now;
        
        if (distance < 0) {
            timerEl.innerHTML = "Время вышло!";
            timerEl.classList.add('timer--danger');
            clearInterval(timerInterval);
            
            // Force submit when time is up
            const form = document.getElementById('test-form');
            if (form) {
                document.getElementById('submit-action-input').name = 'submit_test';
                form.submit();
            }
            return;
        }
        
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        let display = "";
        if (hours > 0) display += (hours < 10 ? "0" + hours : hours) + ":";
        display += (minutes < 10 ? "0" + minutes : minutes) + ":";
        display += (seconds < 10 ? "0" + seconds : seconds);
        
        timerEl.innerHTML = display;
        
        // Warning state: < 15 mins
        if (distance < 15 * 60 * 1000) {
            timerEl.classList.add('timer--warning');
        }
        
        // Danger state: < 5 mins
        if (distance < 5 * 60 * 1000) {
            timerEl.classList.remove('timer--warning');
            timerEl.classList.add('timer--danger');
        }
    }
    
    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);
}

/**
 * Initialize submit confirmation modal
 */
function initSubmitModal() {
    const triggerBtn = document.getElementById('trigger-submit-btn');
    const modal = document.getElementById('submitConfirmModal');
    const cancelBtn = document.getElementById('cancelSubmitBtn');
    const confirmBtn = document.getElementById('confirmSubmitBtn');
    const form = document.getElementById('test-form');
    const submitInput = document.getElementById('submit-action-input');

    if (!triggerBtn || !modal || !cancelBtn || !confirmBtn || !form) return;

    // Open modal
    triggerBtn.addEventListener('click', function(e) {
        e.preventDefault();
        modal.classList.add('active');
    });

    // Close modal on cancel
    cancelBtn.addEventListener('click', function() {
        modal.classList.remove('active');
    });

    // Submit form on confirm
    confirmBtn.addEventListener('click', function() {
        submitInput.name = 'submit_test';
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Отправка...';
        
        // Re-initialize icons for spinner
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        form.submit();
    });

    // Close modal if clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            modal.classList.remove('active');
        }
    });
}