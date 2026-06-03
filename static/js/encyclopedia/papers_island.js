import { fetchScientificPapers } from './papers_api.js';

const { createApp, ref, computed, onMounted } = Vue;

const PAGE_SIZE = 6;

const PapersIsland = {
    setup() {
        const allPapers = ref([]);
        const profile = ref(null);
        const loading = ref(true);
        const error = ref(null);
        const page = ref(1);

        const mountPoint = document.getElementById('papers-island');
        const apiUrl = mountPoint ? mountPoint.getAttribute('data-api-url') : '';

        const visiblePapers = computed(() => allPapers.value.slice(0, page.value * PAGE_SIZE));
        const hasMore = computed(() => allPapers.value.length > page.value * PAGE_SIZE);

        const loadPapers = async () => {
            if (!apiUrl) {
                error.value = 'Не удалось определить источник статей.';
                loading.value = false;
                return;
            }

            try {
                loading.value = true;
                const payload = await fetchScientificPapers(apiUrl, 20);
                allPapers.value = payload.articles;
                profile.value = payload.profile;
            } catch (err) {
                error.value = 'Не удалось загрузить актуальные статьи.';
                console.error(err);
            } finally {
                loading.value = false;
            }
        };

        const loadMore = () => {
            page.value++;
        };

        onMounted(() => loadPapers());

        return { visiblePapers, loading, error, hasMore, loadMore, allPapers, profile };
    },

    template: `
        <div class="papers-island-container">
            <h2 class="papers-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="papers-icon"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                Актуальные научные статьи
            </h2>

            <div v-if="loading" class="papers-loading">
                <div class="skeleton-card" v-for="n in 6" :key="n">
                    <div class="skeleton-title"></div>
                    <div class="skeleton-authors"></div>
                    <div class="skeleton-text"></div>
                    <div class="skeleton-text short"></div>
                </div>
            </div>

            <div v-else-if="error" class="papers-error">{{ error }}</div>

            <div v-else-if="allPapers.length === 0" class="papers-empty">
                По этой теме не найдено достаточно релевантных научных статей.
            </div>

            <template v-else>
                <div class="papers-profile" v-if="profile">
                    <span class="papers-profile-label">Запросы:</span>
                    <span>{{ profile.queryEn }}</span>
                    <span class="papers-profile-divider">/</span>
                    <span>{{ profile.queryRu }}</span>
                </div>

                <div class="papers-grid">
                    <a v-for="paper in visiblePapers" :key="paper.id" :href="paper.url" target="_blank" rel="noopener noreferrer" class="paper-card">
                        <div class="paper-meta">
                            <span class="paper-year">{{ paper.year }}</span>

                            <span v-if="paper.citations > 0" class="paper-citations">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none" class="citation-icon"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                                Цитат: {{ paper.citations }}
                            </span>

                            <span v-if="paper.pdfUrl" class="paper-open-access">PDF</span>

                            <span class="paper-lang-badge" :class="paper.language === 'ru' ? 'lang-ru' : 'lang-en'">
                                {{ paper.language === 'ru' ? 'RU' : 'EN' }}
                            </span>
                        </div>
                        <h3 class="paper-title">{{ paper.title }}</h3>
                        <p class="paper-authors">{{ paper.authors }}</p>
                        <p class="paper-abstract">{{ paper.abstract || 'Аннотация недоступна у источника.' }}</p>
                        <ul class="paper-reasons" v-if="paper.relevanceReasons && paper.relevanceReasons.length">
                            <li v-for="reason in paper.relevanceReasons" :key="reason">{{ reason }}</li>
                        </ul>
                    </a>
                </div>

                <div v-if="hasMore" class="papers-load-more">
                    <button class="btn-load-more" @click="loadMore">
                        Ещё статьи ↓
                    </button>
                </div>
            </template>

            <div class="papers-footer" v-if="!loading && allPapers.length > 0">
                Ранжирование учитывает онтологический контекст, ключевые термины, аннотацию, цитируемость и год публикации.
                Источники:
                <a href="https://www.semanticscholar.org" target="_blank">Semantic Scholar</a> и
                <a href="https://www.crossref.org/" target="_blank">Crossref</a>
            </div>
        </div>
    `
};

if (document.getElementById('papers-island')) {
    createApp(PapersIsland).mount('#papers-island');
}
