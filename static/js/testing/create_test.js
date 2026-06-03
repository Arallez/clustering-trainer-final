document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('taskSearch');
    const typeFilter = document.getElementById('taskTypeFilter');
    const difficultyFilter = document.getElementById('taskDifficultyFilter');
    const items = Array.from(document.querySelectorAll('.task-picker-item'));
    const groups = Array.from(document.querySelectorAll('.task-picker-group'));
    const defaultScoreInput = document.getElementById('id_auto_task_score');

    if (!items.length) return;

    function normalize(value) {
        return (value || '').toString().trim().toLowerCase();
    }

    function syncDefaultScore() {
        const value = defaultScoreInput && defaultScoreInput.value ? defaultScoreInput.value : '1';
        items.forEach((item) => {
            const scoreInput = item.querySelector('input[name^="task_score_"]');
            if (scoreInput && !item.dataset.scoreTouched) {
                scoreInput.value = value;
            }
        });
    }

    function applyFilters() {
        const query = normalize(searchInput ? searchInput.value : '');
        const type = typeFilter ? typeFilter.value : '';
        const difficulty = difficultyFilter ? difficultyFilter.value : '';

        items.forEach((item) => {
            const haystack = [
                item.dataset.title,
                item.dataset.group,
                item.dataset.concept,
            ].join(' ');
            const matchesQuery = !query || haystack.includes(query);
            const matchesType = !type || item.dataset.type === type;
            const matchesDifficulty = !difficulty || item.dataset.difficulty === difficulty;
            item.classList.toggle('is-hidden', !(matchesQuery && matchesType && matchesDifficulty));
        });

        groups.forEach((group) => {
            const visibleItems = Array.from(group.querySelectorAll('.task-picker-item')).some((item) => !item.classList.contains('is-hidden'));
            group.classList.toggle('is-hidden', !visibleItems);
        });
    }

    items.forEach((item) => {
        const scoreInput = item.querySelector('input[name^="task_score_"]');
        const checkbox = item.querySelector('input[type="checkbox"]');
        if (scoreInput) {
            scoreInput.addEventListener('input', () => {
                item.dataset.scoreTouched = '1';
            });
        }
        if (checkbox) {
            checkbox.addEventListener('change', () => {
                item.classList.toggle('task-picker-item--selected', checkbox.checked);
            });
        }
    });

    if (defaultScoreInput) {
        defaultScoreInput.addEventListener('input', syncDefaultScore);
        syncDefaultScore();
    }

    [searchInput, typeFilter, difficultyFilter].forEach((control) => {
        if (control) control.addEventListener('input', applyFilters);
        if (control) control.addEventListener('change', applyFilters);
    });

    applyFilters();
});
