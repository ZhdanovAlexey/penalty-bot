#!/bin/bash

# Скрипт для деплоя Telegram бота на сервер
# Использование: ./deploy.sh

set -e  # Остановить выполнение при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Конфигурация
APP_NAME="penalty-bot"
APP_DIR="/opt/penalty-bot"
SERVICE_NAME="penalty-bot.service"
USER_NAME="penalty-bot"

log "Начинаем деплой Telegram бота..."

# Проверяем, что скрипт запущен с правами root
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен с правами root (sudo)"
   exit 1
fi

# Создаем пользователя для бота (если не существует)
if ! id "$USER_NAME" &>/dev/null; then
    log "Создаем пользователя $USER_NAME..."
    useradd --system --shell /bin/false --home-dir $APP_DIR --create-home $USER_NAME
else
    log "Пользователь $USER_NAME уже существует"
fi

# Создаем директории
log "Создаем необходимые директории..."
mkdir -p $APP_DIR/{data,logs}
chown -R $USER_NAME:$USER_NAME $APP_DIR

# Копируем файлы приложения
log "Копируем файлы приложения..."
cp -r . $APP_DIR/
chown -R $USER_NAME:$USER_NAME $APP_DIR

# Устанавливаем Python и pip (если не установлены)
log "Проверяем установку Python..."
if ! command -v python3 &> /dev/null; then
    log "Устанавливаем Python3..."
    apt update
    apt install -y python3 python3-pip python3-venv
fi

# Создаем виртуальное окружение
log "Создаем виртуальное окружение..."
cd $APP_DIR
sudo -u $USER_NAME python3 -m venv venv
sudo -u $USER_NAME ./venv/bin/pip install --upgrade pip
sudo -u $USER_NAME ./venv/bin/pip install -r requirements.txt

# Проверяем наличие .env файла
if [ ! -f "$APP_DIR/.env" ]; then
    warn ".env файл не найден!"
    warn "Скопируйте env.example в .env и заполните необходимые переменные:"
    warn "cp $APP_DIR/env.example $APP_DIR/.env"
    warn "nano $APP_DIR/.env"
fi

# Устанавливаем systemd service
log "Устанавливаем systemd service..."
cp $APP_DIR/systemd/penalty-bot.service /etc/systemd/system/
systemctl daemon-reload

# Включаем и запускаем сервис
log "Запускаем сервис..."
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

# Проверяем статус
sleep 3
if systemctl is-active --quiet $SERVICE_NAME; then
    log "✅ Сервис успешно запущен!"
    log "Статус сервиса: $(systemctl is-active $SERVICE_NAME)"
else
    error "❌ Ошибка запуска сервиса!"
    error "Проверьте логи: journalctl -u $SERVICE_NAME -f"
    exit 1
fi

log "🎉 Деплой завершен успешно!"
log ""
log "Полезные команды:"
log "  Статус сервиса:     systemctl status $SERVICE_NAME"
log "  Логи сервиса:       journalctl -u $SERVICE_NAME -f"
log "  Перезапуск:         systemctl restart $SERVICE_NAME"
log "  Остановка:          systemctl stop $SERVICE_NAME"
log "  Отключение:         systemctl disable $SERVICE_NAME"
log ""
log "Файлы конфигурации:"
log "  Приложение:         $APP_DIR"
log "  Логи:               $APP_DIR/logs"
log "  База данных:        $APP_DIR/data"
log "  Конфигурация:       $APP_DIR/.env" 