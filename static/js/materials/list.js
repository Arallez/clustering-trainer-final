/**
 * Поиск по карточкам материалов на странице списка.
 * Островковая архитектура: логика в отдельном JS, без инлайна в шаблоне.
 */
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('materialSearch');
    const cards = document.querySelectorAll('.material-card');
    const noResults = document.getElementById('noResults');

    if (!searchInput || !noResults) return;

    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase().trim();
        let visibleCount = 0;

        cards.forEach(function(card) {
            const title = card.getAttribute('data-title');

            if (title && title.indexOf(query) !== -1) {
                card.style.display = 'flex';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    });
});