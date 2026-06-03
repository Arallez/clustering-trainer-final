# Структура проекта

Ниже приведена актуальная структура репозитория с привязкой к модулям, которые используются приложением сейчас.

```text
diploma-clustering-app/
├── apps/                         # Django-приложения с бизнес-логикой
│   ├── core/                     # главная, auth, профиль, custom admin site
│   ├── materials/                # учебные материалы и прогресс чтения
│   ├── encyclopedia/             # онтология, граф знаний, curriculum, рекомендации
│   │   └── data/clustering.owl # активный OWL-файл модуля
│   ├── simulator/                # визуальный симулятор алгоритмов и прогресс симуляций
│   ├── tasks/                    # учебные задания, попытки, проверка решений, sandbox bridge
│   └── testing/                  # группы, тесты, вопросы, сдача и ручная проверка
├── config/                       # настройки Django, корневые URL, WSGI/ASGI
├── docs/                         # документация, диаграммы, справочные материалы
│   ├── assets/design-checks/      # скриншоты и артефакты визуальных проверок
│   └── references/               # внешние PDF/исходные материалы для диплома
├── fixtures/                     # переносимые дампы данных Django
│   └── datadump.json
├── sandbox/                      # Docker-образ и runner песочницы
├── scripts/                      # разовые утилиты обслуживания проекта
├── static/                       # исходные CSS/JS/images/vendor ассеты
├── templates/                    # Django-шаблоны, разложенные по модулям
├── media/                        # локальные пользовательские загрузки, не версионируется
├── staticfiles/                  # результат collectstatic, не версионируется
├── manage.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
└── .env.example
```

## Ключевые каталоги

## `apps/`

Основная бизнес-логика разбита на Django-приложения.

### `apps/core/`

Содержит базовую пользовательскую оболочку сайта.

- `models.py` — `UserProfile`.
- `views.py` — домашняя страница, регистрация, профиль.
- `urls.py` — публичные маршруты корня сайта.
- `admin_site.py` — кастомный `AdminSite`.
- `admin.py` — базовая точка регистрации core-сущностей.

### `apps/materials/`

Отвечает за теоретические материалы и прогресс их изучения.

- `models.py` — `Material`, `MaterialProgress`.
- `views.py` — список материалов, детальная страница, отметки изучения.
- `urls.py` — маршруты `/materials/` и `/materials/<slug>/`.
- `admin.py` — регистрация материалов и прогресса материалов в кастомной админке.
- `migrations/0001_initial.py` — state-only перенос моделей из `core`; существующие таблицы БД сохранены как `core_material` и `core_materialprogress`.

### `apps/encyclopedia/`

Работает с онтологией, графом знаний, редактируемыми модулями курса и рекомендациями.

- `models.py` — `Concept`, `ConceptRelation`, `CourseModule`, `CourseModuleSimulator`.
- `ontology.py` — синхронизация OWL -> БД.
- `curriculum.py` — собирает учебный маршрут из модулей курса, заданных через админку.
- `recommendations.py` — логика адаптивных рекомендаций, mastery концептов и remediation после ошибок.
- `article_profiles.py` — строит профиль темы для поиска научных статей.
- `article_sources.py` — забирает публикации из Semantic Scholar и Crossref.
- `article_ranker.py` — считает внутренний балл релевантности и причины попадания статьи.
- `article_service.py` — собирает профиль, источники, ранжирование и кэширование.
- `views.py` — граф знаний, список понятий, карточка понятия, страница рекомендаций.
- `signals.py` — инвалидирует кэш графа при изменении онтологии.
- `management/commands/` — `sync_ontology`.

### `apps/tasks/`

Практический контур.

- `models.py` — `TaskTag`, `Task`, `UserTaskAttempt`.
- `views.py` — список заданий, карточка задания, проверка ответа, рекомендации для повторения после ошибки.
- `sandbox.py` — безопасное выполнение пользовательского Python-кода, включая несколько тест-кейсов.
- `admin.py` — кастомная форма, `related_concepts` и конструктор quiz-задач.
- `management/commands/load_test_course.py` — тестовое наполнение курса.

### `apps/simulator/`

Интерактивная песочница алгоритмов кластеризации.

- `models.py` — `SimulatorProgress`, прогресс прохождения симуляторных шагов в маршруте.
- `views.py` — HTML-страница симулятора и JSON-эндпоинты.
- `algorithms.py` — реализации алгоритмов и дендрограмм.
- `presets.py` — генерация тестовых датасетов.
- `catalog.py` — соответствие ключей алгоритмов концептам онтологии.
- `services.py` — безопасность выполнения кода для старого/вспомогательного контура.
- `management/commands/check_algorithm_alignment.py` — проверка согласованности алгоритмов, онтологии и задач.

### `apps/testing/`

Контур преподавателя и студентов.

- `models.py` — преподаватели, группы, вопросы, тесты, ответы, попытки.
- `views.py` — создание тестов, вступление в группы, сдача, проверка.
- `urls.py` — маршруты интерфейса тестирования.
- `admin.py` — регистрация всех сущностей в админке.

## `config/`

Конфигурация Django-проекта.

- `settings.py` — настройки БД, приложений, статики, медиа, sandbox.
- `urls.py` — корневой роутинг.
- `wsgi.py`, `asgi.py` — точки входа.

## `templates/`

Шаблоны разделены по пользовательским контурам:

- `templates/core/`
- `templates/materials/`
- `templates/encyclopedia/`
- `templates/tasks/`
- `templates/testing/`
- `templates/simulator/`
- `templates/admin/`
- `templates/includes/`
- `templates/emails/`

## `static/`

Исходная статика проекта.

- `static/css/core/` — базовая оболочка, главная, auth, профиль.
- `static/css/materials/` — список и детальная страница учебных материалов.
- `static/css/tasks/` — список заданий и экран решения.
- `static/css/testing/` — все стили контура тестирования; `index.css` собирает остальные файлы через `@import`.
- `static/css/simulator/` — экран симулятора.
- `static/css/encyclopedia/` — база знаний, граф, рекомендации, виджет статей.
- `static/css/admin/` — кастомная админка и формы.
- `static/css/vendor/` — внешние CSS-зависимости.
- `static/js/core/` — общая клиентская оболочка, частицы, auth, профиль.
- `static/js/materials/` — клиентский поиск по материалам.
- `static/js/tasks/` — интерфейс решения задач.
- `static/js/testing/` — клиентская логика тестирования.
- `static/js/simulator/` — отдельный frontend симулятора.
- `static/js/encyclopedia/` — клиентская логика базы знаний и виджета научных статей.
- `static/js/shared/` — общие помощники, например markdown renderer.
- `static/js/vendor/` — внешние JS-зависимости.
- `static/images/` — изображения и логотипы.

## `sandbox/`

Изолированное окружение для проверки Python-кода.

- `Dockerfile` — образ песочницы.
- `requirements.txt` — зависимости runner.
- `runner.py` — безопасный запуск кода, несколько тест-кейсов и сериализация результата.

## `docs/`

Актуальная документация по модулям проекта.

- `ARCHITECTURE.md`
- `API.md`
- `ADMIN.md`
- `PROJECT_FILE_GUIDE.md`
- `DOCKER.md`
- `ENCYCLOPEDIA.md`
- `HOME_PAGE.md`
- `LEARNING_PATH.md`
- `MATERIALS.md`
- `ONTOLOGY.md`
- `PROFILES.md`
- `SANDBOX.md`
- `SIMULATOR.md`
- `TASKS.md`
- `TESTING.md`

### `docs/assets/design-checks/`

Скриншоты и логи ручных/визуальных проверок интерфейса. Они вынесены из корня, чтобы корневой каталог оставался только для файлов запуска, конфигурации и документации верхнего уровня.

## `scripts/`

Набор разовых утилит. Большинство скриптов исторические и полезны только при ручном восстановлении старых данных.

## Корневые файлы

### `requirements.txt`

Python-зависимости проекта.

### `docker-compose.yml`

Локальный контейнерный запуск:

- PostgreSQL
- Django web
- sandbox image

### `Dockerfile`

Основной образ Django-приложения.

### `entrypoint.sh`

Сценарий запуска в контейнере: миграции, `loaddata`, `collectstatic`, `runserver`.

### `fixtures/datadump.json`

Дамп данных для начального наполнения БД.

### `apps/encyclopedia/data/clustering.owl`

Текущий основной файл онтологии.

## Важные замечания по структуре

- доменные модели задач хранятся в `apps/tasks`, а не в `apps/simulator`;
- `apps/simulator` снова содержит активную модель, но только для прогресса симуляций (`SimulatorProgress`);
- материалы вынесены из `apps/core` в `apps/materials`; физические таблицы оставлены прежними для совместимости данных;
- прогресс чтения материалов хранится в `apps/materials.MaterialProgress`;
- логика рекомендаций находится в `apps/encyclopedia/recommendations.py`, хотя используется и на страницах `core`;
- модульный маршрут обучения хранится в моделях `CourseModule` и `CourseModuleSimulator`, а `apps/encyclopedia/curriculum.py` только собирает его для интерфейса;
- `staticfiles/` не редактируется вручную, это производный каталог;
- `venv/` не относится к проектному коду и не должен учитываться как часть архитектуры;
- в проекте нет каталога с собственными автотестами.
