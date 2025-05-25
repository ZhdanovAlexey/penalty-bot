# 🚀 Инструкция по деплою Telegram бота на VPS

Данная инструкция описывает процесс развертывания бота-калькулятора неустойки по ДДУ на виртуальном сервере.

## 📋 Требования к серверу

### Минимальные требования:
- **ОС**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM**: 512 MB (рекомендуется 1 GB)
- **CPU**: 1 vCPU
- **Диск**: 5 GB свободного места
- **Сеть**: Доступ в интернет

### Необходимое ПО:
- Python 3.9+
- Git
- systemd (для автозапуска)

## 🛠 Способы деплоя

### Способ 1: Автоматический деплой (рекомендуется)

#### 1. Подготовка сервера
```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
sudo apt install -y git curl wget nano htop
```

#### 2. Клонирование проекта
```bash
# Клонируем репозиторий
git clone https://github.com/ZhdanovAlexey/penalty-bot.git penalty-bot-deploy
cd penalty-bot-deploy
```

#### 3. Настройка конфигурации
```bash
# Копируем пример конфигурации
cp env.example .env

# Редактируем конфигурацию
nano .env
```

Заполните следующие переменные:
```env
BOT_TOKEN=your_telegram_bot_token_here
SPREADSHEET_ID=your_google_spreadsheet_id_here
SHEET_NAME=Лист1
```

#### 4. Настройка Google Sheets API
```bash
# Создайте директорию для данных
mkdir -p data

# Скопируйте файл service_account.json в data/
# Получить его можно в Google Cloud Console
```

#### 5. Запуск автоматического деплоя
```bash
# Делаем скрипт исполняемым
chmod +x scripts/deploy.sh

# Запускаем деплой
sudo ./scripts/deploy.sh
```

### Способ 2: Ручной деплой

#### 1. Создание пользователя
```bash
sudo useradd --system --shell /bin/false --home-dir /opt/penalty-bot --create-home penalty-bot
```

#### 2. Установка приложения
```bash
# Копируем файлы
sudo cp -r . /opt/penalty-bot/
sudo chown -R penalty-bot:penalty-bot /opt/penalty-bot

# Переходим в директорию
cd /opt/penalty-bot
```

#### 3. Создание виртуального окружения
```bash
# Создаем venv
sudo -u penalty-bot python3 -m venv venv

# Устанавливаем зависимости
sudo -u penalty-bot ./venv/bin/pip install --upgrade pip
sudo -u penalty-bot ./venv/bin/pip install -r requirements.txt
```

#### 4. Настройка systemd
```bash
# Копируем service файл
sudo cp systemd/penalty-bot.service /etc/systemd/system/

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable penalty-bot.service

# Запускаем сервис
sudo systemctl start penalty-bot.service
```

### Способ 3: Docker деплой

#### 1. Установка Docker
```bash
# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Устанавливаем Docker Compose
sudo apt install -y docker-compose
```

#### 2. Настройка конфигурации
```bash
# Создаем .env файл
cp env.example .env
nano .env

# Создаем директории для данных
mkdir -p data logs
```

#### 3. Запуск через Docker Compose
```bash
# Собираем и запускаем контейнер
sudo docker-compose up -d

# Проверяем статус
sudo docker-compose ps
sudo docker-compose logs -f
```

## 🔧 Настройка Google Sheets API

### 1. Создание проекта в Google Cloud Console
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API

### 2. Создание Service Account
1. Перейдите в "IAM & Admin" → "Service Accounts"
2. Нажмите "Create Service Account"
3. Заполните имя и описание
4. Нажмите "Create and Continue"
5. Добавьте роль "Editor" или "Viewer" (в зависимости от потребностей)
6. Нажмите "Done"

### 3. Создание ключа
1. Найдите созданный Service Account
2. Нажмите на него и перейдите во вкладку "Keys"
3. Нажмите "Add Key" → "Create new key"
4. Выберите формат JSON
5. Скачайте файл и переименуйте его в `service_account.json`
6. Поместите файл в директорию `data/`

### 4. Настройка доступа к таблице
1. Откройте скачанный JSON файл
2. Найдите поле `client_email`
3. Скопируйте email адрес
4. Откройте вашу Google Таблицу
5. Нажмите "Поделиться" и добавьте этот email с правами "Редактор" или "Читатель"

## 📊 Управление сервисом

### Основные команды
```bash
# Статус сервиса
sudo systemctl status penalty-bot

# Запуск сервиса
sudo systemctl start penalty-bot

# Остановка сервиса
sudo systemctl stop penalty-bot

# Перезапуск сервиса
sudo systemctl restart penalty-bot

# Включить автозапуск
sudo systemctl enable penalty-bot

# Отключить автозапуск
sudo systemctl disable penalty-bot
```

### Просмотр логов
```bash
# Просмотр логов в реальном времени
sudo journalctl -u penalty-bot -f

# Просмотр последних логов
sudo journalctl -u penalty-bot -n 100

# Просмотр логов за сегодня
sudo journalctl -u penalty-bot --since today
```

## 🔄 Обновление бота

### Автоматическое обновление
```bash
# Переходим в директорию с проектом
cd /path/to/penalty-bot-deploy

# Получаем последние изменения
git pull

# Запускаем скрипт обновления
sudo ./scripts/update.sh
```

### Ручное обновление
```bash
# Останавливаем сервис
sudo systemctl stop penalty-bot

# Создаем бэкап
sudo cp -r /opt/penalty-bot /opt/penalty-bot-backup-$(date +%Y%m%d)

# Обновляем код (сохраняя конфигурацию и данные)
sudo rsync -av --exclude='.env' --exclude='data/' --exclude='venv/' . /opt/penalty-bot/

# Обновляем зависимости
cd /opt/penalty-bot
sudo -u penalty-bot ./venv/bin/pip install -r requirements.txt

# Запускаем сервис
sudo systemctl start penalty-bot
```

## 🔒 Безопасность

### Рекомендации по безопасности:
1. **Файрвол**: Настройте UFW или iptables
```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
```

2. **Обновления**: Регулярно обновляйте систему
```bash
sudo apt update && sudo apt upgrade -y
```

3. **Мониторинг**: Настройте мониторинг логов
```bash
# Установка fail2ban для защиты от брутфорса
sudo apt install -y fail2ban
```

4. **Бэкапы**: Настройте автоматические бэкапы
```bash
# Пример скрипта бэкапа
#!/bin/bash
tar -czf /backup/penalty-bot-$(date +%Y%m%d).tar.gz /opt/penalty-bot/data
```

## 🐛 Устранение неполадок

### Частые проблемы:

#### 1. Бот не запускается
```bash
# Проверяем логи
sudo journalctl -u penalty-bot -n 50

# Проверяем конфигурацию
cat /opt/penalty-bot/.env

# Проверяем права доступа
ls -la /opt/penalty-bot/
```

#### 2. Ошибки Google Sheets API
```bash
# Проверяем наличие файла ключа
ls -la /opt/penalty-bot/data/service_account.json

# Проверяем права доступа к файлу
sudo chown penalty-bot:penalty-bot /opt/penalty-bot/data/service_account.json
```

#### 3. Проблемы с базой данных
```bash
# Проверяем права на директорию data
sudo chown -R penalty-bot:penalty-bot /opt/penalty-bot/data

# Проверяем наличие базы данных
ls -la /opt/penalty-bot/data/
```

### Полезные команды для диагностики:
```bash
# Проверка использования ресурсов
htop

# Проверка места на диске
df -h

# Проверка сетевых соединений
netstat -tulpn

# Проверка процессов Python
ps aux | grep python
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи сервиса
2. Убедитесь в правильности конфигурации
3. Проверьте доступность Google Sheets API
4. Обратитесь к разработчику с подробным описанием проблемы

## 📝 Дополнительные настройки

### Настройка логирования
Для более детального логирования можно настроить ротацию логов:

```bash
# Создаем конфигурацию logrotate
sudo nano /etc/logrotate.d/penalty-bot
```

Содержимое файла:
```
/opt/penalty-bot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 penalty-bot penalty-bot
    postrotate
        systemctl reload penalty-bot
    endscript
}
```

### Мониторинг производительности
Для мониторинга можно использовать различные инструменты:

```bash
# Установка htop для мониторинга ресурсов
sudo apt install -y htop

# Установка iotop для мониторинга дисковых операций
sudo apt install -y iotop

# Мониторинг сетевой активности
sudo apt install -y nethogs
``` 