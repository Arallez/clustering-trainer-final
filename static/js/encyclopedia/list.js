/**
 * Поиск по карточкам понятий на странице списка энциклопедии.
 * Островковая архитектура: логика в отдельном JS, без инлайна в шаблоне.
 */
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('conceptSearch');
    const cards = document.querySelectorAll('.concept-card');
    const noResults = document.getElementById('noResults');

    if (!searchInput || !noResults) return;

    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase().trim();
        let visibleCount = 0;

        cards.forEach(function(card) {
            const title = card.getAttribute('data-title');
            const desc = card.getAttribute('data-desc');

            if ((title && title.indexOf(query) !== -1) || (desc && desc.indexOf(query) !== -1)) {
                card.style.display = 'flex';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    });
});
