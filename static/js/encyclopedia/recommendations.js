/**
 * Recommendations Page Logic
 */

document.addEventListener('DOMContentLoaded', function() {
  // Apply progress bar width from data attribute
  const progressBar = document.querySelector('.progress-bar');
  if (progressBar) {
    const progress = progressBar.dataset.progress || 0;
    progressBar.style.width = progress + '%';
  }
});