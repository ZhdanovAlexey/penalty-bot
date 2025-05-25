#!/bin/bash

# Скрипт для создания бэкапов Telegram бота
# Использование: ./backup.sh [full|data]

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
DATE_STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_TYPE="${1:-data}"  # По умолчанию только данные

# Функция для создания директории бэкапов
create_backup_dir() {
    if [ ! -d "$BACKUP_BASE_DIR" ]; then
        log "Создаем директорию для бэкапов: $BACKUP_BASE_DIR"
        mkdir -p "$BACKUP_BASE_DIR"
        chmod 755 "$BACKUP_BASE_DIR"
    fi
}

# Функция для проверки существования приложения
check_app_exists() {
    if [ ! -d "$APP_DIR" ]; then
        error "Приложение не найдено в $APP_DIR"
        error "Возможно, бот еще не развернут или путь неверный"
        exit 1
    fi
}

# Функция для очистки старых бэкапов (оставляем последние 7)
cleanup_old_backups() {
    local backup_pattern="$1"
    local keep_count=7
    
    log "Очистка старых бэкапов (оставляем последние $keep_count)..."
    
    # Находим и удаляем старые бэкапы
    find "$BACKUP_BASE_DIR" -name "$backup_pattern" -type f | \
    sort -r | \
    tail -n +$((keep_count + 1)) | \
    while read -r old_backup; do
        log "Удаляем старый бэкап: $(basename "$old_backup")"
        rm -f "$old_backup"
    done
}

# Функция для создания бэкапа данных
backup_data() {
    local backup_file="$BACKUP_BASE_DIR/penalty-bot-data-$DATE_STAMP.tar.gz"
    
    log "Создаем бэкап данных..."
    
    if [ ! -d "$APP_DIR/data" ]; then
        warn "Директория данных $APP_DIR/data не найдена"
        return 1
    fi
    
    # Создаем архив данных
    tar -czf "$backup_file" -C "$APP_DIR" data/ 2>/dev/null || {
        error "Ошибка создания архива данных"
        return 1
    }
    
    local size=$(du -h "$backup_file" | cut -f1)
    log "✅ Бэкап данных создан: $(basename "$backup_file") ($size)"
    
    # Очищаем старые бэкапы данных
    cleanup_old_backups "penalty-bot-data-*.tar.gz"
    
    return 0
}

# Функция для создания полного бэкапа
backup_full() {
    local backup_file="$BACKUP_BASE_DIR/penalty-bot-full-$DATE_STAMP.tar.gz"
    
    log "Создаем полный бэкап приложения..."
    
    # Создаем полный архив (исключаем временные файлы и venv)
    tar -czf "$backup_file" \
        --exclude="$APP_DIR/venv" \
        --exclude="$APP_DIR/logs/*.log" \
        --exclude="$APP_DIR/__pycache__" \
        --exclude="$APP_DIR/.git" \
        -C "$(dirname "$APP_DIR")" \
        "$(basename "$APP_DIR")" 2>/dev/null || {
        error "Ошибка создания полного архива"
        return 1
    }
    
    local size=$(du -h "$backup_file" | cut -f1)
    log "✅ Полный бэкап создан: $(basename "$backup_file") ($size)"
    
    # Очищаем старые полные бэкапы
    cleanup_old_backups "penalty-bot-full-*.tar.gz"
    
    return 0
}

# Функция для создания бэкапа конфигурации
backup_config() {
    local backup_file="$BACKUP_BASE_DIR/penalty-bot-config-$DATE_STAMP.tar.gz"
    
    log "Создаем бэкап конфигурации..."
    
    # Создаем временную директорию для конфигурации
    local temp_dir=$(mktemp -d)
    
    # Копируем важные конфигурационные файлы
    [ -f "$APP_DIR/.env" ] && cp "$APP_DIR/.env" "$temp_dir/"
    [ -f "$APP_DIR/data/service_account.json" ] && cp "$APP_DIR/data/service_account.json" "$temp_dir/"
    
    if [ "$(ls -A "$temp_dir")" ]; then
        tar -czf "$backup_file" -C "$temp_dir" . 2>/dev/null
        local size=$(du -h "$backup_file" | cut -f1)
        log "✅ Бэкап конфигурации создан: $(basename "$backup_file") ($size)"
    else
        warn "Конфигурационные файлы не найдены"
    fi
    
    # Очищаем временную директорию
    rm -rf "$temp_dir"
    
    return 0
}

# Функция для отображения статистики бэкапов
show_backup_stats() {
    log "📊 Статистика бэкапов:"
    echo ""
    
    if [ -d "$BACKUP_BASE_DIR" ]; then
        local total_size=$(du -sh "$BACKUP_BASE_DIR" 2>/dev/null | cut -f1)
        local backup_count=$(find "$BACKUP_BASE_DIR" -name "*.tar.gz" -type f | wc -l)
        
        echo "📁 Директория бэкапов: $BACKUP_BASE_DIR"
        echo "📦 Всего бэкапов: $backup_count"
        echo "💾 Общий размер: $total_size"
        echo ""
        
        if [ $backup_count -gt 0 ]; then
            echo "📋 Последние бэкапы:"
            find "$BACKUP_BASE_DIR" -name "*.tar.gz" -type f -printf "%T@ %p\n" | \
            sort -nr | \
            head -5 | \
            while read -r timestamp filepath; do
                local date_str=$(date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r "$timestamp" '+%Y-%m-%d %H:%M:%S')
                local size=$(du -h "$filepath" | cut -f1)
                echo "  $(basename "$filepath") - $date_str ($size)"
            done
        fi
    else
        echo "Директория бэкапов не найдена"
    fi
}

# Основная функция
main() {
    echo -e "${BLUE}🗄️  Система бэкапов Penalty Bot${NC}"
    echo ""
    
    # Проверяем права доступа
    if [[ $EUID -ne 0 ]]; then
        error "Этот скрипт должен быть запущен с правами root (sudo)"
        exit 1
    fi
    
    # Создаем директорию для бэкапов
    create_backup_dir
    
    # Проверяем существование приложения
    check_app_exists
    
    case "$BACKUP_TYPE" in
        "data")
            backup_data
            ;;
        "full")
            backup_full
            ;;
        "config")
            backup_config
            ;;
        "all")
            backup_data
            backup_config
            backup_full
            ;;
        "stats")
            show_backup_stats
            exit 0
            ;;
        *)
            echo "Использование: $0 [data|full|config|all|stats]"
            echo ""
            echo "Типы бэкапов:"
            echo "  data   - Только данные (база данных, файлы)"
            echo "  config - Только конфигурация (.env, ключи API)"
            echo "  full   - Полный бэкап приложения"
            echo "  all    - Все типы бэкапов"
            echo "  stats  - Показать статистику бэкапов"
            exit 1
            ;;
    esac
    
    echo ""
    show_backup_stats
    
    log "🎉 Бэкап завершен успешно!"
}

# Запуск основной функции
main "$@" 