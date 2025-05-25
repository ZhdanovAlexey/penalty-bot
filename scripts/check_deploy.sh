#!/bin/bash

# Скрипт для проверки готовности проекта к деплою
# Использование: ./check_deploy.sh

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}✅ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo -e "${BLUE}🔍 Проверка готовности проекта к деплою...${NC}"
echo ""

# Счетчики
ERRORS=0
WARNINGS=0

# Проверка основных файлов
echo "📁 Проверка структуры проекта:"

if [ -f "bot.py" ]; then
    log "bot.py найден"
else
    error "bot.py не найден"
    ((ERRORS++))
fi

if [ -f "requirements.txt" ]; then
    log "requirements.txt найден"
else
    error "requirements.txt не найден"
    ((ERRORS++))
fi

if [ -f "config.py" ]; then
    log "config.py найден"
else
    error "config.py не найден"
    ((ERRORS++))
fi

if [ -d "handlers" ]; then
    log "Директория handlers найдена"
else
    error "Директория handlers не найдена"
    ((ERRORS++))
fi

if [ -d "services" ]; then
    log "Директория services найдена"
else
    error "Директория services не найдена"
    ((ERRORS++))
fi

echo ""

# Проверка конфигурационных файлов
echo "⚙️  Проверка конфигурации:"

if [ -f "env.example" ]; then
    log "env.example найден"
else
    error "env.example не найден"
    ((ERRORS++))
fi

if [ -f ".env" ]; then
    log ".env файл найден"
    
    # Проверка обязательных переменных
    if grep -q "BOT_TOKEN=" .env && ! grep -q "BOT_TOKEN=your_bot_token_here" .env; then
        log "BOT_TOKEN настроен"
    else
        error "BOT_TOKEN не настроен в .env"
        ((ERRORS++))
    fi
    
    if grep -q "SPREADSHEET_ID=" .env && ! grep -q "SPREADSHEET_ID=your_google_spreadsheet_id_here" .env; then
        log "SPREADSHEET_ID настроен"
    else
        error "SPREADSHEET_ID не настроен в .env"
        ((ERRORS++))
    fi
else
    warn ".env файл не найден (будет создан из env.example при деплое)"
    ((WARNINGS++))
fi

echo ""

# Проверка Google Sheets credentials
echo "🔑 Проверка Google Sheets API:"

if [ -d "data" ]; then
    log "Директория data найдена"
    
    if [ -f "data/service_account.json" ]; then
        log "service_account.json найден"
        
        # Проверка валидности JSON
        if python3 -m json.tool data/service_account.json > /dev/null 2>&1; then
            log "service_account.json валиден"
        else
            error "service_account.json содержит некорректный JSON"
            ((ERRORS++))
        fi
    else
        error "data/service_account.json не найден"
        info "Создайте Service Account в Google Cloud Console и поместите JSON файл в data/"
        ((ERRORS++))
    fi
else
    warn "Директория data не найдена (будет создана при деплое)"
    ((WARNINGS++))
fi

echo ""

# Проверка деплой файлов
echo "🚀 Проверка файлов деплоя:"

if [ -f "Dockerfile" ]; then
    log "Dockerfile найден"
else
    warn "Dockerfile не найден (Docker деплой недоступен)"
    ((WARNINGS++))
fi

if [ -f "docker-compose.yml" ]; then
    log "docker-compose.yml найден"
else
    warn "docker-compose.yml не найден (Docker Compose деплой недоступен)"
    ((WARNINGS++))
fi

if [ -f "systemd/penalty-bot.service" ]; then
    log "systemd service файл найден"
else
    error "systemd/penalty-bot.service не найден"
    ((ERRORS++))
fi

if [ -f "scripts/deploy.sh" ]; then
    log "Скрипт деплоя найден"
    if [ -x "scripts/deploy.sh" ]; then
        log "Скрипт деплоя исполняемый"
    else
        warn "Скрипт деплоя не исполняемый (chmod +x scripts/deploy.sh)"
        ((WARNINGS++))
    fi
else
    error "scripts/deploy.sh не найден"
    ((ERRORS++))
fi

if [ -f "scripts/update.sh" ]; then
    log "Скрипт обновления найден"
    if [ -x "scripts/update.sh" ]; then
        log "Скрипт обновления исполняемый"
    else
        warn "Скрипт обновления не исполняемый (chmod +x scripts/update.sh)"
        ((WARNINGS++))
    fi
else
    error "scripts/update.sh не найден"
    ((ERRORS++))
fi

echo ""

# Проверка Python зависимостей
echo "🐍 Проверка Python зависимостей:"

if command -v python3 &> /dev/null; then
    log "Python3 найден: $(python3 --version)"
else
    error "Python3 не найден"
    ((ERRORS++))
fi

if [ -f "requirements.txt" ]; then
    # Проверка основных зависимостей
    if grep -q "aiogram" requirements.txt; then
        log "aiogram найден в requirements.txt"
    else
        error "aiogram не найден в requirements.txt"
        ((ERRORS++))
    fi
    
    if grep -q "google-api-python-client" requirements.txt; then
        log "google-api-python-client найден в requirements.txt"
    else
        error "google-api-python-client не найден в requirements.txt"
        ((ERRORS++))
    fi
fi

echo ""

# Проверка документации
echo "📚 Проверка документации:"

if [ -f "README.md" ]; then
    log "README.md найден"
else
    warn "README.md не найден"
    ((WARNINGS++))
fi

if [ -f "DEPLOYMENT.md" ]; then
    log "DEPLOYMENT.md найден"
else
    warn "DEPLOYMENT.md не найден"
    ((WARNINGS++))
fi

if [ -f "QUICK_START.md" ]; then
    log "QUICK_START.md найден"
else
    warn "QUICK_START.md не найден"
    ((WARNINGS++))
fi

echo ""

# Итоговый отчет
echo "📊 Итоговый отчет:"
echo "=================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 Проект полностью готов к деплою!${NC}"
    echo ""
    echo "Следующие шаги:"
    echo "1. Загрузите проект на сервер"
    echo "2. Запустите: sudo ./scripts/deploy.sh"
    echo "3. Проверьте работу: sudo systemctl status penalty-bot"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Проект готов к деплою с предупреждениями${NC}"
    echo -e "${YELLOW}Предупреждений: $WARNINGS${NC}"
    echo ""
    echo "Проект можно деплоить, но рекомендуется исправить предупреждения."
else
    echo -e "${RED}❌ Проект НЕ готов к деплою${NC}"
    echo -e "${RED}Ошибок: $ERRORS${NC}"
    echo -e "${YELLOW}Предупреждений: $WARNINGS${NC}"
    echo ""
    echo "Исправьте ошибки перед деплоем."
    exit 1
fi

echo ""
echo "Для деплоя используйте:"
echo "  Автоматический: sudo ./scripts/deploy.sh"
echo "  Docker:         sudo docker-compose up -d"
echo "  Ручной:         см. DEPLOYMENT.md" 