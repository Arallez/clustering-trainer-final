/**
 * Admin Dashboard - Vue.js Application
 * Современная панель администратора
 */

const { createApp, ref, computed, onMounted } = Vue;

createApp({
    setup() {
        // Состояние - на мобильных меню закрыто по умолчанию, на ПК - открыто
        const isMobile = window.innerWidth <= 1024;
        const sidebarOpen = ref(!isMobile);
        const currentTime = ref(new Date());
        const isLoading = ref(true);
        
        // Получаем данные из Django
        const adminData = window.adminData || {
            materialsCount: 0,
            tasksCount: 0,
            testsCount: 0,
            conceptsCount: 0,
            userName: 'Администратор'
        };
        const adminUrls = adminData.urls || {};
        
        // Данные статистики
        const stats = ref([
            {
                id: 'materials',
                label: 'Материалы',
                value: adminData.materialsCount,
                icon: 'book-open',
                color: 'primary',
                trend: null,
                trendValue: null
            },
            {
                id: 'tasks',
                label: 'Задания',
                value: adminData.tasksCount,
                icon: 'code',
                color: 'accent',
                trend: null,
                trendValue: null
            },
            {
                id: 'tests',
                label: 'Тесты',
                value: adminData.testsCount,
                icon: 'file-check',
                color: 'warning',
                trend: null,
                trendValue: null
            },
            {
                id: 'concepts',
                label: 'Концепты',
                value: adminData.conceptsCount,
                icon: 'network',
                color: 'success',
                trend: null,
                trendValue: null
            }
        ]);
        
        // Модули админки
        const modules = ref([
            {
                id: 'materials',
                title: 'Материалы',
                description: 'Учебные материалы и статьи по кластеризации',
                icon: 'book-open',
                iconClass: 'materials',
                count: adminData.materialsCount,
                url: adminUrls.materials || '/admin/core/material/'
            },
            {
                id: 'tasks',
                title: 'Задания',
                description: 'Задания для практической работы студентов',
                icon: 'code',
                iconClass: 'tasks',
                count: adminData.tasksCount,
                url: adminUrls.tasks || '/admin/tasks/task/'
            },
            {
                id: 'tags',
                title: 'Теги заданий',
                description: 'Категории и теги для организации заданий',
                icon: 'tag',
                iconClass: 'tasks',
                count: 0,
                url: adminUrls.taskTags || '/admin/tasks/tasktag/'
            },
            {
                id: 'tests',
                title: 'Тестирование',
                description: 'Управление тестами и вопросами',
                icon: 'file-check',
                iconClass: 'testing',
                count: adminData.testsCount,
                url: adminUrls.tests || '/admin/testing/test/'
            },
            {
                id: 'concepts',
                title: 'Энциклопедия',
                description: 'Концепты и связи между ними',
                icon: 'network',
                iconClass: 'encyclopedia',
                count: adminData.conceptsCount,
                url: adminUrls.concepts || '/admin/encyclopedia/concept/'
            }
        ]);
        
        // Последняя активность
        const recentActivity = ref([]);
        
        // Имя пользователя
        const userName = ref(adminData.userName);
        const userInitials = computed(() => {
            return userName.value
                .split(' ')
                .map(n => n[0])
                .join('')
                .toUpperCase()
                .slice(0, 2);
        });
        
        // Форматирование времени
        const formattedTime = computed(() => {
            return currentTime.value.toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit'
            });
        });
        
        const formattedDate = computed(() => {
            return currentTime.value.toLocaleDateString('ru-RU', {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
                year: 'numeric'
            });
        });
        
        // Методы
        const toggleSidebar = () => {
            sidebarOpen.value = !sidebarOpen.value;
            const sidebar = document.querySelector('.admin-sidebar');
            const wrapper = document.querySelector('.admin-wrapper');
            const overlay = document.querySelector('.admin-sidebar-overlay');
            
            if (window.innerWidth <= 1024) {
                // На мобильных - используем класс open
                sidebar?.classList.toggle('open', sidebarOpen.value);
                overlay?.classList.toggle('active', sidebarOpen.value);
            } else {
                // На ПК - используем класс sidebar-collapsed на wrapper
                wrapper?.classList.toggle('sidebar-collapsed', !sidebarOpen.value);
            }
            
            // Обновляем иконки Lucide после изменения DOM
            if (window.lucide) {
                window.lucide.createIcons();
            }
        };
        
        // Слушаем изменение размера окна
        const handleResize = () => {
            const newIsMobile = window.innerWidth <= 1024;
            if (newIsMobile !== isMobile) {
                window.location.reload(); // Перезагружаем при смене режима
            }
        };
        
        const updateTime = () => {
            currentTime.value = new Date();
        };
        
        // Инициализация
        onMounted(async () => {
            // Обновляем время каждую минуту
            setInterval(updateTime, 60000);
            
            // Скрываем загрузку
            setTimeout(() => {
                isLoading.value = false;
            }, 300);
            
            // Инициализируем иконки Lucide
            if (window.lucide) {
                window.lucide.createIcons();
            }
        });
        
        return {
            sidebarOpen,
            currentTime,
            isLoading,
            stats,
            modules,
            recentActivity,
            userName,
            userInitials,
            formattedTime,
            formattedDate,
            toggleSidebar
        };
    }
}).mount('#admin-app');
