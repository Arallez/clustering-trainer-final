# Docker и контейнерный запуск

Проект поддерживает локальный запуск через Docker Compose. Этот режим поднимает PostgreSQL, Django-приложение и, при необходимости, образ sandbox для проверки пользовательского Python-кода.

## Файлы

- `docker-compose.yml`
- `Dockerfile`
- `entrypoint.sh`
- `sandbox/Dockerfile`

## Сервисы в `docker-compose.yml`

### `db`

PostgreSQL 14 Alpine.

Параметры по умолчанию:

- `POSTGRES_DB=clustering_db`
- `POSTGRES_USER=admin`
- `POSTGRES_PASSWORD=secretpassword`

Порт:

- `5432:5432`

Для сервиса настроен `healthcheck`, чтобы `web` стартовал после готовности базы.

### `web`

Основной контейнер Django-приложения.

Особенности:

- строится из корневого `Dockerfile`;
- монтирует проект как volume в `/app`;
- монтирует Docker socket внутрь контейнера;
- использует переменные окружения для БД и sandbox;
- публикует порт `8000`.

Порт:

- `8000:8000`

Переменные окружения:

```env
DB_NAME=clustering_db
DB_USER=admin
DB_PASSWORD=secretpassword
DB_HOST=db
DB_PORT=5432
SECRET_KEY=django-insecure-docker-dev-key-change-in-production
DEBUG=True
SANDBOX_EXECUTOR=docker
SANDBOX_IMAGE=clustering-sandbox:latest
SANDBOX_ALLOW_INPROCESS_FALLBACK=True
```

### `sandbox`

Отдельный образ песочницы выполнения кода.

Особенности:

- строится из `sandbox/Dockerfile`;
- тегируется как `clustering-sandbox:latest`;
- находится в compose-профиле `sandbox`;
- запускается с `sleep infinity`, потому что backend создает рабочие sandbox-контейнеры динамически;
- сеть отключена через `network_mode: "none"`;
- файловая система read-only.

## Запуск

Обычный запуск:

```bash
docker compose up --build
```

Запуск с предварительной сборкой sandbox-образа:

```bash
docker compose --profile sandbox up --build
```

После старта сайт доступен по адресу:

```text
http://localhost:8000/
```

## Что делает `Dockerfile`

Основной образ:

1. берет `python:3.11-slim`;
2. устанавливает системные пакеты `gcc` и `libpq-dev`;
3. копирует `requirements.txt`;
4. устанавливает Python-зависимости;
5. копирует код проекта;
6. открывает порт `8000`;
7. запускает миграции, загрузку фикстур, сбор статики и `runserver`.

Команда запуска сейчас задана прямо в `Dockerfile`:

```bash
python manage.py migrate --noinput && \
python manage.py loaddata fixtures/datadump.json 2>/dev/null; \
python manage.py collectstatic --noinput && \
python manage.py runserver 0.0.0.0:8000
```

Из-за `;` после `loaddata` ошибки загрузки фикстур не останавливают запуск сервера.

## `entrypoint.sh`

В репозитории также есть `entrypoint.sh`, который делает почти тот же сценарий:

1. ждет базу;
2. применяет миграции;
3. пытается загрузить `fixtures/datadump.json`;
4. собирает статику;
5. запускает сервер.

На текущем этапе compose использует команду из `Dockerfile`, а `entrypoint.sh` остается альтернативным сценарным файлом.

## Почему `web` монтирует Docker socket

При `SANDBOX_EXECUTOR=docker` кодовые задания проверяются через `apps.tasks.sandbox._run_in_docker()`.

Backend создает отдельные sandbox-контейнеры через Python Docker SDK. Поэтому контейнер `web` должен иметь доступ к:

```text
/var/run/docker.sock
```

Без этого:

- Docker-режим sandbox не сможет подключиться к daemon;
- кодовые задания будут работать только в `inprocess`-режиме, если разрешен fallback;
- при отключенном fallback проверка кодовых задач будет возвращать ошибку sandbox.

## Данные и миграции

При старте `web`:

- выполняется `python manage.py migrate --noinput`;
- выполняется попытка `python manage.py loaddata fixtures/datadump.json`;
- выполняется `python manage.py collectstatic --noinput`.

Новые миграции прогресса материалов, учебного маршрута и симулятора применяются тем же общим механизмом:

- `apps/core/migrations/0006_materialprogress.py`;
- `apps/materials/migrations/0001_initial.py`;
- `apps/core/migrations/0007_move_materials_to_materials_app.py`;
- `apps/simulator/migrations/0011_simulatorprogress.py`;
- `apps/encyclopedia/migrations/0005_course_modules.py`;
- `apps/encyclopedia/migrations/0006_course_module_simulator_choices.py`;
- миграции `apps/tasks`, связанные с curriculum и `related_concepts`.

Важно: приложение материалов сейчас называется `apps.materials`, но таблицы `core_material` и `core_materialprogress` сохранены намеренно. Это state-only перенос моделей, а не удаление и повторное создание данных.

## Ограничения текущего Docker-сценария

- используется `runserver`, а не production WSGI-сервер;
- в compose прописаны dev-пароли и `DEBUG=True`;
- `loaddata fixtures/datadump.json` вызывается на старте каждый раз, а ошибки скрываются;
- `entrypoint.sh` и команда в `Dockerfile` частично дублируют друг друга;
- Docker socket внутри `web` удобен для локальной разработки, но требует осторожности за пределами локального окружения.

Для дипломной или локальной демонстрации этого достаточно, но для production-сборки конфигурацию нужно ужесточать.

Перед показом на чистой машине стоит отдельно проверить:

1. `docker compose up --build`;
2. применение всех миграций с нуля;
3. загрузку `fixtures/datadump.json`;
4. доступность `/`, `/materials/`, `/tasks/`, `/encyclopedia/`, `/simulator/`, `/testing/`;
5. работу sandbox-режима, если ожидается проверка кодовых задач через Docker.

## Оценка текущей реализации

Для локальной демонстрации запуск реализован приемлемо: `docker compose up --build` поднимает базу и Django, миграции применяются автоматически, статика собирается, а при наличии sandbox-образа кодовые задания могут исполняться в контейнерной песочнице.

Но как инженерное решение мне эта схема нравится только частично.

Что сделано удачно:

- есть отдельная PostgreSQL-служба с `healthcheck`;
- зависимости ставятся на этапе сборки образа, а не при каждом старте;
- sandbox вынесен в отдельный Dockerfile и запускается под отдельным пользователем;
- в Django есть fallback на `inprocess`, поэтому локальный запуск не обязательно ломается, если Docker sandbox недоступен.

Что выглядит слабым местом:

- `docker compose up --build` без профиля не собирает `clustering-sandbox:latest`, хотя `web` запускается с `SANDBOX_EXECUTOR=docker`;
- команда `CMD` в `Dockerfile` слишком длинная и смешивает миграции, фикстуры, collectstatic и сервер;
- из-за `;` после `loaddata` часть ошибок может быть скрыта, а сценарий продолжит выполнение;
- `entrypoint.sh` существует, но фактически не используется compose-файлом;
- Docker socket монтируется внутрь `web`, что удобно для дипломного стенда, но это сильное расширение прав контейнера;
- dev-секреты, dev-пароли и `DEBUG=True` зашиты прямо в compose;
- используется `runserver`, хотя в зависимостях уже есть `gunicorn`;
- нет отдельного production-like профиля без volume-монтажа исходников и без fallback на `inprocess`.

Как бы я улучшил:

1. Использовать `entrypoint.sh` явно через `ENTRYPOINT` или `command`, чтобы сценарий запуска был в одном месте.
2. Разделить команды: миграции/фикстуры отдельно, запуск сервера отдельно, без скрытия неожиданных ошибок.
3. Либо убрать профиль `sandbox`, либо документировать основной запуск как `docker compose --profile sandbox up --build`, чтобы sandbox-образ точно собирался.
4. Для демонстрации оставить `runserver`, но добавить отдельный production-like command через `gunicorn`.
5. Вынести пароли и `SECRET_KEY` в `.env`, а в compose оставить только безопасные значения по умолчанию или ссылки на переменные.
6. Отдельно описать риск Docker socket и не использовать такую схему за пределами локального стенда.

Мой вердикт: для дипломной локальной демонстрации — нормально и практично; для аккуратной эксплуатации — сыровато. Самое важное исправление перед показом проекта: сделать запуск sandbox предсказуемым, чтобы кодовые задачи не зависели от того, был ли образ `clustering-sandbox:latest` случайно собран раньше.
