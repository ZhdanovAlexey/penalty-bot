#!/bin/bash

# Скрипт для настройки автоматических бэкапов через cron
# Использование: ./setup_cron_backup.sh

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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"
CRON_USER="root"

echo -e "${BLUE}⏰ Настройка автоматических бэкапов${NC}"
echo ""

# Проверяем права доступа
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен с правами root (sudo)"
   exit 1
fi

# Проверяем существование скрипта бэкапа
if [ ! -f "$BACKUP_SCRIPT" ]; then
    error "Скрипт бэкапа не найден: $BACKUP_SCRIPT"
    exit 1
fi

# Делаем скрипт бэкапа исполняемым
chmod +x "$BACKUP_SCRIPT"
log "Скрипт бэкапа сделан исполняемым"

# Функция для добавления задачи в cron
add_cron_job() {
    local schedule="$1"
    local command="$2"
    local description="$3"
    
    # Проверяем, существует ли уже такая задача
    if crontab -u "$CRON_USER" -l 2>/dev/null | grep -q "$command"; then
        warn "Задача уже существует: $description"
        return 0
    fi
    
    # Добавляем новую задачу
    (crontab -u "$CRON_USER" -l 2>/dev/null; echo "$schedule $command # $description") | crontab -u "$CRON_USER" -
    log "✅ Добавлена задача: $description"
}

# Настройка расписания бэкапов
log "Настраиваем расписание бэкапов..."

# Ежедневный бэкап данных в 2:00
add_cron_job "0 2 * * *" "$BACKUP_SCRIPT data >/dev/null 2>&1" "Daily data backup"

# Еженедельный полный бэкап в воскресенье в 3:00
add_cron_job "0 3 * * 0" "$BACKUP_SCRIPT full >/dev/null 2>&1" "Weekly full backup"

# Ежемесячный бэкап конфигурации в первый день месяца в 4:00
add_cron_job "0 4 1 * *" "$BACKUP_SCRIPT config >/dev/null 2>&1" "Monthly config backup"

echo ""
log "📋 Текущие задачи cron для бэкапов:"
crontab -u "$CRON_USER" -l 2>/dev/null | grep "$BACKUP_SCRIPT" || echo "Нет задач"

echo ""
log "📅 Расписание бэкапов:"
echo "  🔄 Ежедневно в 02:00 - бэкап данных"
echo "  📦 Еженедельно (воскресенье) в 03:00 - полный бэкап"
echo "  ⚙️  Ежемесячно (1 число) в 04:00 - бэкап конфигурации"

echo ""
log "🎉 Автоматические бэкапы настроены!"

# Создаем скрипт для ручного управления бэкапами
cat > /usr/local/bin/penalty-backup << 'EOF'
#!/bin/bash
# Удобная команда для управления бэкапами
SCRIPT_DIR="/opt/penalty-bot/scripts"
exec "$SCRIPT_DIR/backup.sh" "$@"
EOF

chmod +x /usr/local/bin/penalty-backup
log "✅ Создана команда 'penalty-backup' для ручного управления"

echo ""
info "💡 Полезные команды:"
echo "  penalty-backup data    - Создать бэкап данных"
echo "  penalty-backup full    - Создать полный бэкап"
echo "  penalty-backup config  - Создать бэкап конфигурации"
echo "  penalty-backup all     - Создать все типы бэкапов"
echo "  penalty-backup stats   - Показать статистику бэкапов"
echo ""
echo "  crontab -l             - Показать все задачи cron"
echo "  systemctl status crond - Проверить статус cron (CentOS/RHEL)"
echo "  systemctl status cron  - Проверить статус cron (Ubuntu/Debian)" 