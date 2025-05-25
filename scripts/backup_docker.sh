#!/bin/bash

# Специальный скрипт для бэкапов в Docker-окружении
# Использование: ./backup_docker.sh [data|full|volumes]

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

# Функция для автоматического определения расположения приложения
detect_app_dir() {
    local possible_dirs=(
        "/home/ubuntu/penalty-bot"
        "/opt/penalty-bot"
        "$(pwd)"
        "$(dirname "$(pwd)")"
    )
    
    for dir in "${possible_dirs[@]}"; do
        if [ -d "$dir" ] && [ -f "$dir/bot.py" ]; then
            echo "$dir"
            return 0
        fi
    done
    
    return 1
}

# Конфигурация
APP_DIR=$(detect_app_dir)
if [ -z "$APP_DIR" ]; then
    error "Не удалось найти приложение penalty-bot"
    exit 1
fi

BACKUP_BASE_DIR="/var/backups/penalty-bot"
DATE_STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_TYPE="${1:-data}"

log "Обнаружено приложение в: $APP_DIR"

# Функция для создания директории бэкапов
create_backup_dir() {
    if [ ! -d "$BACKUP_BASE_DIR" ]; then
        log "Создаем директорию для бэкапов: $BACKUP_BASE_DIR"
        mkdir -p "$BACKUP_BASE_DIR"
        chmod 755 "$BACKUP_BASE_DIR"
    fi
}

# Функция для получения имени Docker контейнера
get_container_name() {
    local container_name=""
    
    # Ищем контейнер по разным паттернам
    if command -v docker >/dev/null 2>&1; then
        container_name=$(docker ps --filter "name=penalty" --format "{{.Names}}" | head -1)
        
        if [ -z "$container_name" ]; then
            container_name=$(docker ps --filter "name=bot" --format "{{.Names}}" | head -1)
        fi
        
        if [ -z "$container_name" ]; then
            # Ищем по образу
            container_name=$(docker ps --format "{{.Names}}" | grep -E "(penalty|bot)" | head -1)
        fi
    fi
    
    echo "$container_name"
}

# Функция для бэкапа данных из Docker контейнера
backup_docker_data() {
    local backup_file="$BACKUP_BASE_DIR/penalty-bot-docker-data-$DATE_STAMP.tar.gz"
    local container_name=$(get_container_name)
    
    log "Создаем бэкап данных из Docker контейнера..."
    
    if [ -n "$container_name" ]; then
        log "Найден контейнер: $container_name"
        
        # Создаем бэкап данных из контейнера
        docker exec "$container_name" tar -czf /tmp/backup-data.tar.gz /app/data 2>/dev/null || \
        docker exec "$container_name" tar -czf /tmp/backup-data.tar.gz /data 2>/dev/null || \
        docker exec "$container_name" tar -czf /tmp/backup-data.tar.gz ./data 2>/dev/null || {
            warn "Не удалось создать бэкап из контейнера, пробуем локальную директорию"
            backup_local_data
            return $?
        }
        
        # Копируем бэкап из контейнера
        docker cp "$container_name:/tmp/backup-data.tar.gz" "$backup_file" || {
            error "Ошибка копирования бэкапа из контейнера"
            return 1
        }
        
        # Очищаем временный файл в контейнере
        docker exec "$container_name" rm -f /tmp/backup-data.tar.gz 2>/dev/null || true
        
    else
        warn "Docker контейнер не найден, создаем бэкап локальной директории"
        backup_local_data
        return $?
    fi
    
    local size=$(du -h "$backup_file" | cut -f1)
    log "✅ Бэкап данных создан: $(basename "$backup_file") ($size)"
    
    return 0
}

# Функция для бэкапа локальных данных
backup_local_data() {
    local backup_file="$BACKUP_BASE_DIR/penalty-bot-local-data-$DATE_STAMP.tar.gz"
    
    if [ ! -d "$APP_DIR/data" ]; then
        warn "Директория данных $APP_DIR/data не найдена, создаем пустую"
        mkdir -p "$APP_DIR/data"
    fi
    
    tar -czf "$backup_file" -C "$APP_DIR" data/ 2>/dev/null || {
        error "Ошибка создания архива данных"
        return 1
    }
    
    local size=$(du -h "$backup_file" | cut -f1)
    log "✅ Бэкап локальных данных создан: $(basename "$backup_file") ($size)"
    
    return 0
}

# Функция для бэкапа Docker volumes
backup_docker_volumes() {
    local backup_file="$BACKUP_BASE_DIR/penalty-bot-volumes-$DATE_STAMP.tar.gz"
    
    log "Создаем бэкап Docker volumes..."
    
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker не установлен"
        return 1
    fi
    
    # Ищем volumes связанные с penalty-bot
    local volumes=$(docker volume ls --filter "name=penalty" --format "{{.Name}}")
    
    if [ -z "$volumes" ]; then
        volumes=$(docker volume ls --filter "name=bot" --format "{{.Name}}")
    fi
    
    if [ -z "$volumes" ]; then
        warn "Docker volumes не найдены"
        return 1
    fi
    
    # Создаем временный контейнер для бэкапа volumes
    local temp_container="penalty-backup-$(date +%s)"
    
    echo "$volumes" | while read -r volume; do
        if [ -n "$volume" ]; then
            log "Создаем бэкап volume: $volume"
            docker run --rm \
                -v "$volume:/data" \
                -v "$BACKUP_BASE_DIR:/backup" \
                --name "$temp_container" \
                alpine tar -czf "/backup/volume-$volume-$DATE_STAMP.tar.gz" /data 2>/dev/null || \
                warn "Не удалось создать бэкап volume: $volume"
        fi
    done
    
    log "✅ Бэкап Docker volumes завершен"
    return 0
}

# Функция для полного бэкапа
backup_full() {
    local backup_file="$BACKUP_BASE_DIR/penalty-bot-docker-full-$DATE_STAMP.tar.gz"
    
    log "Создаем полный бэкап приложения..."
    
    # Создаем полный архив локальной директории
    tar -czf "$backup_file" \
        --exclude="$APP_DIR/venv" \
        --exclude="$APP_DIR/.venv" \
        --exclude="$APP_DIR/logs/*.log" \
        --exclude="$APP_DIR/__pycache__" \
        --exclude="$APP_DIR/.git" \
        --exclude="$APP_DIR/node_modules" \
        -C "$(dirname "$APP_DIR")" \
        "$(basename "$APP_DIR")" 2>/dev/null || {
        error "Ошибка создания полного архива"
        return 1
    }
    
    local size=$(du -h "$backup_file" | cut -f1)
    log "✅ Полный бэкап создан: $(basename "$backup_file") ($size)"
    
    return 0
}

# Функция для отображения статистики
show_stats() {
    log "📊 Статистика бэкапов Docker-окружения:"
    echo ""
    
    echo "📁 Директория приложения: $APP_DIR"
    echo "📁 Директория бэкапов: $BACKUP_BASE_DIR"
    
    # Информация о Docker
    if command -v docker >/dev/null 2>&1; then
        local container_name=$(get_container_name)
        if [ -n "$container_name" ]; then
            echo "🐳 Docker контейнер: $container_name"
            echo "📊 Статус контейнера: $(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null || echo "неизвестен")"
        else
            echo "🐳 Docker контейнер: не найден"
        fi
        
        local volumes=$(docker volume ls --filter "name=penalty" --format "{{.Name}}" | wc -l)
        echo "💾 Docker volumes: $volumes"
    else
        echo "🐳 Docker: не установлен"
    fi
    
    echo ""
    
    if [ -d "$BACKUP_BASE_DIR" ]; then
        local total_size=$(du -sh "$BACKUP_BASE_DIR" 2>/dev/null | cut -f1)
        local backup_count=$(find "$BACKUP_BASE_DIR" -name "*.tar.gz" -type f | wc -l)
        
        echo "📦 Всего бэкапов: $backup_count"
        echo "💾 Общий размер: $total_size"
        echo ""
        
        if [ $backup_count -gt 0 ]; then
            echo "📋 Последние бэкапы:"
            find "$BACKUP_BASE_DIR" -name "*.tar.gz" -type f -printf "%T@ %p\n" 2>/dev/null | \
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
    echo -e "${BLUE}🐳 Система бэкапов Penalty Bot (Docker)${NC}"
    echo ""
    
    # Проверяем права доступа
    if [[ $EUID -ne 0 ]]; then
        error "Этот скрипт должен быть запущен с правами root (sudo)"
        exit 1
    fi
    
    # Создаем директорию для бэкапов
    create_backup_dir
    
    case "$BACKUP_TYPE" in
        "data")
            backup_docker_data
            ;;
        "full")
            backup_full
            ;;
        "volumes")
            backup_docker_volumes
            ;;
        "all")
            backup_docker_data
            backup_full
            backup_docker_volumes
            ;;
        "stats")
            show_stats
            exit 0
            ;;
        *)
            echo "Использование: $0 [data|full|volumes|all|stats]"
            echo ""
            echo "Типы бэкапов для Docker:"
            echo "  data     - Данные из Docker контейнера или локальной директории"
            echo "  full     - Полный бэкап локальной директории приложения"
            echo "  volumes  - Бэкап Docker volumes"
            echo "  all      - Все типы бэкапов"
            echo "  stats    - Показать статистику бэкапов"
            exit 1
            ;;
    esac
    
    echo ""
    show_stats
    
    log "🎉 Бэкап завершен успешно!"
}

# Запуск основной функции
main "$@" 