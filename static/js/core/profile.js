/**
 * Profile Page Logic
 */

document.addEventListener('DOMContentLoaded', function() {
    // Apply progress bar width from data attribute
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        const progress = progressFill.dataset.progress || 0;
        progressFill.style.width = progress + '%';
    }
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Initialize particles
    if (typeof initParticles === 'function') {
        initParticles();
    }
});