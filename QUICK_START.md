# ⚡ Быстрый старт - Деплой бота на VPS

## 🚀 За 5 минут до запуска

### 1. Подготовка сервера
```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Git
sudo apt install -y git
```

### 2. Клонирование и настройка
```bash
# Клонируем проект
git clone https://github.com/ZhdanovAlexey/penalty-bot.git penalty-bot
cd penalty-bot

# Настраиваем конфигурацию
cp env.example .env
nano .env  # Заполните BOT_TOKEN и SPREADSHEET_ID
```

### 3. Настройка Google Sheets
1. Создайте Service Account в [Google Cloud Console](https://console.cloud.google.com/)
2. Скачайте JSON ключ и поместите в `data/service_account.json`
3. Поделитесь Google таблицей с email из JSON файла

### 4. Автоматический деплой
```bash
# Запускаем автоматический деплой
chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh
```

### 5. Проверка работы
```bash
# Проверяем статус
sudo systemctl status penalty-bot

# Смотрим логи
sudo journalctl -u penalty-bot -f
```

## 🔄 Обновление
```bash
git pull
sudo ./scripts/update.sh
```

## 📊 Управление
```bash
# Перезапуск
sudo systemctl restart penalty-bot

# Остановка
sudo systemctl stop penalty-bot

# Логи
sudo journalctl -u penalty-bot -f
```

## 🆘 Помощь
Подробная инструкция: [DEPLOYMENT.md](DEPLOYMENT.md) 