# ✅ Чек-лист деплоя Telegram бота

## 📋 Подготовка к деплою

### 1. Локальная подготовка
- [ ] Проект протестирован локально
- [ ] Все зависимости указаны в `requirements.txt`
- [ ] Создан файл `.env` с настройками
- [ ] Настроен Google Sheets API
- [ ] Файл `service_account.json` помещен в `data/`
- [ ] Запущена проверка: `./scripts/check_deploy.sh`

### 2. Подготовка сервера
- [ ] Сервер обновлен: `sudo apt update && sudo apt upgrade -y`
- [ ] Установлен Git: `sudo apt install -y git`
- [ ] Настроен SSH доступ
- [ ] Настроен файрвол (опционально)

### 3. Telegram Bot
- [ ] Бот создан через @BotFather
- [ ] Получен BOT_TOKEN
- [ ] Бот добавлен в канал (если нужна проверка подписки)
- [ ] Проверены права бота в канале

### 4. Google Sheets API
- [ ] Создан проект в Google Cloud Console
- [ ] Включен Google Sheets API
- [ ] Создан Service Account
- [ ] Скачан JSON ключ
- [ ] Service Account добавлен в Google таблицу с правами доступа

## 🚀 Процесс деплоя

### Способ 1: Автоматический деплой (рекомендуется)

```bash
# 1. Клонирование проекта
git clone <repository-url> penalty-bot
cd penalty-bot

# 2. Настройка конфигурации
cp env.example .env
nano .env  # Заполнить BOT_TOKEN и SPREADSHEET_ID

# 3. Добавление Google Sheets ключа
# Поместить service_account.json в data/

# 4. Проверка готовности
./scripts/check_deploy.sh

# 5. Запуск деплоя
sudo ./scripts/deploy.sh
```

### Способ 2: Docker деплой

```bash
# 1. Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt install -y docker-compose

# 2. Настройка и запуск
cp env.example .env
nano .env
mkdir -p data logs
# Поместить service_account.json в data/
sudo docker-compose up -d
```

## ✅ Проверка после деплоя

### 1. Проверка сервиса
- [ ] Сервис запущен: `sudo systemctl status penalty-bot`
- [ ] Нет ошибок в логах: `sudo journalctl -u penalty-bot -f`
- [ ] Бот отвечает в Telegram

### 2. Функциональная проверка
- [ ] Команда `/start` работает
- [ ] Проверка подписки работает (если настроена)
- [ ] Расчет неустойки выполняется корректно
- [ ] Google Sheets API работает
- [ ] База данных создается и работает

### 3. Мониторинг
- [ ] Настроен мониторинг логов
- [ ] Проверена автозагрузка сервиса
- [ ] Настроены бэкапы (опционально)

## 🔧 Полезные команды

### Управление сервисом
```bash
# Статус
sudo systemctl status penalty-bot

# Перезапуск
sudo systemctl restart penalty-bot

# Остановка
sudo systemctl stop penalty-bot

# Логи
sudo journalctl -u penalty-bot -f
```

### Обновление
```bash
cd /path/to/project
git pull
sudo ./scripts/update.sh
```

### Диагностика
```bash
# Проверка ресурсов
htop

# Проверка места на диске
df -h

# Проверка сетевых соединений
netstat -tulpn | grep python
```

## 🆘 Устранение проблем

### Частые ошибки:

#### 1. Бот не запускается
```bash
# Проверить логи
sudo journalctl -u penalty-bot -n 50

# Проверить конфигурацию
cat /opt/penalty-bot/.env

# Проверить права
ls -la /opt/penalty-bot/
```

#### 2. Ошибки Google Sheets
```bash
# Проверить файл ключа
ls -la /opt/penalty-bot/data/service_account.json

# Проверить права
sudo chown penalty-bot:penalty-bot /opt/penalty-bot/data/service_account.json
```

#### 3. Проблемы с базой данных
```bash
# Проверить права на data
sudo chown -R penalty-bot:penalty-bot /opt/penalty-bot/data

# Проверить наличие БД
ls -la /opt/penalty-bot/data/
```

## 📞 Контакты поддержки

При возникновении проблем:
1. Проверьте логи сервиса
2. Убедитесь в правильности конфигурации
3. Проверьте доступность внешних API
4. Обратитесь к разработчику с подробным описанием

## 🔄 Регулярное обслуживание

### Еженедельно:
- [ ] Проверка логов на ошибки
- [ ] Мониторинг использования ресурсов
- [ ] Проверка работоспособности бота

### Ежемесячно:
- [ ] Обновление системы: `sudo apt update && sudo apt upgrade`
- [ ] Проверка и очистка логов
- [ ] Создание бэкапа данных

### По необходимости:
- [ ] Обновление бота: `git pull && sudo ./scripts/update.sh`
- [ ] Обновление зависимостей Python
- [ ] Ротация ключей API (если требуется) 