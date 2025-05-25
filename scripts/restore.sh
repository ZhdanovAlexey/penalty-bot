#!/bin/bash

# Скрипт для восстановления из бэкапов Telegram бота
# Использование: ./restore.sh [backup_file]

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Конфигурация
APP_DIR="/opt/penalty-bot"
BACKUP_BASE_DIR="/var/backups/penalty-bot"
BACKUP_FILE="$1"

# Функция для отображения доступных бэкапов
show_available_backups() {
    log "📋 Доступные бэкапы:"
    echo ""
    
    if [ ! -d "$BACKUP_BASE_DIR" ]; then
        error "Директория бэкапов не найдена: $BACKUP_BASE_DIR"
        return 1
    fi
    
    local backup_count=0
    
    # Показываем бэкапы данных
    echo "🗃️  Бэкапы данных:"
    find "$BACKUP_BASE_DIR" -name "penalty-bot-data-*.tar.gz" -type f -printf "%T@ %p\n" 2>/dev/null | \
    sort -nr | \
    head -10 | \
    while read -r timestamp filepath; do
        local date_str=$(date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r "$timestamp" '+%Y-%m-%d %H:%M:%S')
        local size=$(du -h "$filepath" | cut -f1)
        echo "  $(basename "$filepath") - $date_str ($size)"
        backup_count=$((backup_count + 1))
    done
    
    echo ""
    
    # Показываем полные бэкапы
    echo "📦 Полные бэкапы:"
    find "$BACKUP_BASE_DIR" -name "penalty-bot-full-*.tar.gz" -type f -printf "%T@ %p\n" 2>/dev/null | \
    sort -nr | \
    head -5 | \
    while read -r timestamp filepath; do
        local date_str=$(date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r "$timestamp" '+%Y-%m-%d %H:%M:%S')
        local size=$(du -h "$filepath" | cut -f1)
        echo "  $(basename "$filepath") - $date_str ($size)"
    done
    
    echo ""
    
    # Показываем бэкапы конфигурации
    echo "⚙️  Бэкапы конфигурации:"
    find "$BACKUP_BASE_DIR" -name "penalty-bot-config-*.tar.gz" -type f -printf "%T@ %p\n" 2>/dev/null | \
    sort -nr | \
    head -5 | \
    while read -r timestamp filepath; do
        local date_str=$(date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r "$timestamp" '+%Y-%m-%d %H:%M:%S')
        local size=$(du -h "$filepath" | cut -f1)
        echo "  $(basename "$filepath") - $date_str ($size)"
    done
}

# Функция для определения типа бэкапа
get_backup_type() {
    local backup_file="$1"
    local filename=$(basename "$backup_file")
    
    if [[ "$filename" == *"data"* ]]; then
        echo "data"
    elif [[ "$filename" == *"full"* ]]; then
        echo "full"
    elif [[ "$filename" == *"config"* ]]; then
        echo "config"
    else
        echo "unknown"
    fi
}

# Функция для создания резервной копии перед восстановлением
create_pre_restore_backup() {
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_file="$BACKUP_BASE_DIR/penalty-bot-pre-restore-$timestamp.tar.gz"
    
    log "Создаем резервную копию перед восстановлением..."
    
    if [ -d "$APP_DIR" ]; then
        tar -czf "$backup_file" \
            --exclude="$APP_DIR/venv" \
            --exclude="$APP_DIR/logs/*.log" \
            --exclude="$APP_DIR/__pycache__" \
            --exclude="$APP_DIR/.git" \
            -C "$(dirname "$APP_DIR")" \
            "$(basename "$APP_DIR")" 2>/dev/null || {
            warn "Не удалось создать резервную копию"
            return 1
        }
        
        local size=$(du -h "$backup_file" | cut -f1)
        log "✅ Резервная копия создана: $(basename "$backup_file") ($size)"
    else
        warn "Приложение не найдено, резервная копия не создана"
    fi
}

# Функция для остановки бота
stop_bot() {
    log "Останавливаем бота..."
    
    if systemctl is-active --quiet penalty-bot 2>/dev/null; then
        systemctl stop penalty-bot
        log "✅ Бот остановлен"
    else
        warn "Сервис penalty-bot не запущен или не найден"
    fi
}

# Функция для запуска бота
start_bot() {
    log "Запускаем бота..."
    
    if systemctl is-enabled --quiet penalty-bot 2>/dev/null; then
        systemctl start penalty-bot
        sleep 3
        
        if systemctl is-active --quiet penalty-bot; then
            log "✅ Бот запущен успешно"
        else
            error "Не удалось запустить бота"
            return 1
        fi
    else
        warn "Сервис penalty-bot не настроен"
    fi
}

# Функция для восстановления данных
restore_data() {
    local backup_file="$1"
    
    log "Восстанавливаем данные из: $(basename "$backup_file")"
    
    # Создаем директорию приложения если не существует
    mkdir -p "$APP_DIR"
    
    # Извлекаем данные
    tar -xzf "$backup_file" -C "$APP_DIR" || {
        error "Ошибка извлечения данных"
        return 1
    }
    
    # Устанавливаем правильные права доступа
    chown -R root:root "$APP_DIR/data"
    chmod -R 755 "$APP_DIR/data"
    
    log "✅ Данные восстановлены"
}

# Функция для восстановления полного бэкапа
restore_full() {
    local backup_file="$1"
    
    log "Восстанавливаем полный бэкап из: $(basename "$backup_file")"
    
    # Удаляем старую директорию (кроме venv и логов)
    if [ -d "$APP_DIR" ]; then
        # Сохраняем важные директории
        local temp_dir=$(mktemp -d)
        [ -d "$APP_DIR/venv" ] && mv "$APP_DIR/venv" "$temp_dir/" 2>/dev/null || true
        [ -d "$APP_DIR/logs" ] && mv "$APP_DIR/logs" "$temp_dir/" 2>/dev/null || true
        
        # Удаляем старую директорию
        rm -rf "$APP_DIR"
        
        # Извлекаем полный бэкап
        tar -xzf "$backup_file" -C "$(dirname "$APP_DIR")" || {
            error "Ошибка извлечения полного бэкапа"
            return 1
        }
        
        # Восстанавливаем сохраненные директории
        [ -d "$temp_dir/venv" ] && mv "$temp_dir/venv" "$APP_DIR/" 2>/dev/null || true
        [ -d "$temp_dir/logs" ] && mv "$temp_dir/logs" "$APP_DIR/" 2>/dev/null || true
        
        # Очищаем временную директорию
        rm -rf "$temp_dir"
    else
        # Просто извлекаем если директории не было
        tar -xzf "$backup_file" -C "$(dirname "$APP_DIR")" || {
            error "Ошибка извлечения полного бэкапа"
            return 1
        }
    fi
    
    # Устанавливаем правильные права доступа
    chown -R root:root "$APP_DIR"
    chmod +x "$APP_DIR"/*.py 2>/dev/null || true
    chmod +x "$APP_DIR/scripts"/*.sh 2>/dev/null || true
    
    log "✅ Полный бэкап восстановлен"
}

# Функция для восстановления конфигурации
restore_config() {
    local backup_file="$1"
    
    log "Восстанавливаем конфигурацию из: $(basename "$backup_file")"
    
    # Создаем временную директорию
    local temp_dir=$(mktemp -d)
    
    # Извлекаем конфигурацию
    tar -xzf "$backup_file" -C "$temp_dir" || {
        error "Ошибка извлечения конфигурации"
        rm -rf "$temp_dir"
        return 1
    }
    
    # Копируем файлы конфигурации
    [ -f "$temp_dir/.env" ] && cp "$temp_dir/.env" "$APP_DIR/" && log "✅ Восстановлен .env"
    [ -f "$temp_dir/service_account.json" ] && cp "$temp_dir/service_account.json" "$APP_DIR/data/" && log "✅ Восстановлен service_account.json"
    
    # Устанавливаем правильные права доступа
    [ -f "$APP_DIR/.env" ] && chmod 600 "$APP_DIR/.env"
    [ -f "$APP_DIR/data/service_account.json" ] && chmod 600 "$APP_DIR/data/service_account.json"
    
    # Очищаем временную директорию
    rm -rf "$temp_dir"
    
    log "✅ Конфигурация восстановлена"
}

# Функция для подтверждения действия
confirm_restore() {
    local backup_file="$1"
    local backup_type="$2"
    
    echo ""
    warn "⚠️  ВНИМАНИЕ: Восстановление из бэкапа!"
    echo ""
    echo "Файл бэкапа: $(basename "$backup_file")"
    echo "Тип бэкапа: $backup_type"
    echo "Размер: $(du -h "$backup_file" | cut -f1)"
    echo ""
    
    case "$backup_type" in
        "data")
            echo "Будут восстановлены: база данных и файлы данных"
            ;;
        "full")
            echo "Будет восстановлено: все приложение (код, данные, конфигурация)"
            ;;
        "config")
            echo "Будут восстановлены: файлы конфигурации (.env, ключи API)"
            ;;
    esac
    
    echo ""
    read -p "Продолжить восстановление? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Восстановление отменено"
        exit 0
    fi
}

# Основная функция
main() {
    echo -e "${BLUE}🔄 Восстановление из бэкапа Penalty Bot${NC}"
    echo ""
    
    # Проверяем права доступа
    if [[ $EUID -ne 0 ]]; then
        error "Этот скрипт должен быть запущен с правами root (sudo)"
        exit 1
    fi
    
    # Если файл бэкапа не указан, показываем доступные
    if [ -z "$BACKUP_FILE" ]; then
        show_available_backups
        echo ""
        echo "Использование: $0 <backup_file>"
        echo "Пример: $0 /var/backups/penalty-bot/penalty-bot-data-20241225-120000.tar.gz"
        exit 1
    fi
    
    # Проверяем существование файла бэкапа
    if [ ! -f "$BACKUP_FILE" ]; then
        # Пробуем найти файл в директории бэкапов
        if [ -f "$BACKUP_BASE_DIR/$BACKUP_FILE" ]; then
            BACKUP_FILE="$BACKUP_BASE_DIR/$BACKUP_FILE"
        else
            error "Файл бэкапа не найден: $BACKUP_FILE"
            exit 1
        fi
    fi
    
    # Определяем тип бэкапа
    local backup_type=$(get_backup_type "$BACKUP_FILE")
    if [ "$backup_type" = "unknown" ]; then
        error "Неизвестный тип бэкапа: $(basename "$BACKUP_FILE")"
        exit 1
    fi
    
    # Подтверждение
    confirm_restore "$BACKUP_FILE" "$backup_type"
    
    # Создаем резервную копию
    create_pre_restore_backup
    
    # Останавливаем бота
    stop_bot
    
    # Восстанавливаем в зависимости от типа
    case "$backup_type" in
        "data")
            restore_data "$BACKUP_FILE"
            ;;
        "full")
            restore_full "$BACKUP_FILE"
            ;;
        "config")
            restore_config "$BACKUP_FILE"
            ;;
    esac
    
    # Запускаем бота
    start_bot
    
    echo ""
    log "🎉 Восстановление завершено успешно!"
    
    # Показываем статус
    if systemctl is-active --quiet penalty-bot 2>/dev/null; then
        log "✅ Бот работает нормально"
    else
        warn "⚠️  Проверьте статус бота: systemctl status penalty-bot"
    fi
}

# Запуск основной функции
main "$@" 