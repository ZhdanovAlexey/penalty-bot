# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директорию для данных
RUN mkdir -p data

# Устанавливаем права на директорию данных
RUN chmod 755 data

# Указываем порт (не обязательно для бота, но хорошая практика)
EXPOSE 8000

# Команда запуска
CMD ["python", "bot.py"] 