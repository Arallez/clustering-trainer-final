/**
 * Универсальный рендерер Markdown и KaTeX (очень быстрый аналог MathJax)
 */
function renderMarkdownAndMath() {
    if (typeof marked === 'undefined') {
        console.warn('marked.js not loaded');
        return;
    }

    marked.setOptions({
        breaks: true,
        gfm: true
    });

    function cleanIndent(text) {
        if (!text) return '';
        let result = text.trim();
        let lines = result.split('\n');
        
        let minIndent = Infinity;
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].trim().length > 0) {
                const match = lines[i].match(/^[ \t]*/);
                if (match && match[0].length < minIndent) {
                    minIndent = match[0].length;
                }
            }
        }
        
        if (minIndent > 0 && minIndent !== Infinity) {
            const re = new RegExp('^[ \\t]{' + minIndent + '}', 'gm');
            result = result.replace(re, '');
        }
        return result;
    }

    const elements = document.querySelectorAll('.markdown-content');

    // 1. Рендерим Markdown (мгновенно)
    elements.forEach(el => {
        const rawContent = cleanIndent(el.textContent || el.innerText || '');
        el.innerHTML = marked.parse(rawContent);
        
        el.style.opacity = '1';
        el.style.visibility = 'visible';
    });

    // 2. Рендерим математику через KaTeX (в десятки раз быстрее MathJax)
    if (typeof renderMathInElement === 'function') {
        elements.forEach(el => {
            renderMathInElement(el, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\(', right: '\\)', display: false},
                    {left: '\\[', right: '\\]', display: true}
                ],
                throwOnError: false // если формула с ошибкой, просто покажет как текст
            });
        });
    }
}

// Запуск при загрузке
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderMarkdownAndMath);
} else {
    // DOM уже загружен
    renderMarkdownAndMath();
}
