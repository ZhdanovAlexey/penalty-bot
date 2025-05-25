#!/bin/bash

# Скрипт для обновления Telegram бота
# Использование: ./update.sh

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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
APP_DIR="/opt/penalty-bot"
SERVICE_NAME="penalty-bot.service"
USER_NAME="penalty-bot"
BACKUP_DIR="/opt/penalty-bot-backup-$(date +%Y%m%d-%H%M%S)"

log "Начинаем обновление бота..."

# Проверяем права
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен с правами root (sudo)"
   exit 1
fi

# Создаем бэкап
log "Создаем бэкап текущей версии..."
cp -r $APP_DIR $BACKUP_DIR
log "Бэкап создан: $BACKUP_DIR"

# Останавливаем сервис
log "Останавливаем сервис..."
systemctl stop $SERVICE_NAME

# Обновляем код (сохраняем важные файлы)
log "Обновляем код..."
cp $APP_DIR/.env /tmp/penalty-bot.env 2>/dev/null || warn ".env файл не найден"
cp -r $APP_DIR/data /tmp/penalty-bot-data 2>/dev/null || warn "Директория data не найдена"

# Копируем новые файлы (исключая данные)
rsync -av --exclude='.env' --exclude='data/' --exclude='logs/' --exclude='venv/' . $APP_DIR/
chown -R $USER_NAME:$USER_NAME $APP_DIR

# Восстанавливаем важные файлы
cp /tmp/penalty-bot.env $APP_DIR/.env 2>/dev/null || warn "Не удалось восстановить .env"
cp -r /tmp/penalty-bot-data $APP_DIR/data 2>/dev/null || warn "Не удалось восстановить data"

# Обновляем зависимости
log "Обновляем зависимости..."
cd $APP_DIR
sudo -u $USER_NAME ./venv/bin/pip install --upgrade pip
sudo -u $USER_NAME ./venv/bin/pip install -r requirements.txt

# Обновляем systemd service
log "Обновляем systemd service..."
cp $APP_DIR/systemd/penalty-bot.service /etc/systemd/system/
systemctl daemon-reload

# Запускаем сервис
log "Запускаем сервис..."
systemctl start $SERVICE_NAME

# Проверяем статус
sleep 3
if systemctl is-active --quiet $SERVICE_NAME; then
    log "✅ Обновление завершено успешно!"
    log "Сервис запущен и работает"
    
    # Очищаем временные файлы
    rm -f /tmp/penalty-bot.env
    rm -rf /tmp/penalty-bot-data
    
    log "Бэкап сохранен в: $BACKUP_DIR"
    log "Для удаления бэкапа: rm -rf $BACKUP_DIR"
else
    error "❌ Ошибка запуска сервиса после обновления!"
    error "Восстанавливаем из бэкапа..."
    
    systemctl stop $SERVICE_NAME
    rm -rf $APP_DIR
    mv $BACKUP_DIR $APP_DIR
    systemctl start $SERVICE_NAME
    
    error "Бэкап восстановлен. Проверьте логи: journalctl -u $SERVICE_NAME -f"
    exit 1
fi

log "🎉 Обновление завершено!" 