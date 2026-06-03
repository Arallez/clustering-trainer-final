# Используем официальный легкий образ Python 3.11 (для совместимости с whitenoise)
FROM python:3.11-slim

# Устанавливаем системные пакеты для компиляции библиотек (scikit-learn, psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем папку для проекта внутри контейнера
WORKDIR /app

# Копируем список зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта
COPY . .

# Открываем порт 8000
EXPOSE 8000

# Делаем entrypoint.sh исполняемым и запускаем его
RUN chmod +x entrypoint.sh
CMD ["sh", "entrypoint.sh"]
