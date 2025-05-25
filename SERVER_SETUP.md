# 🚀 Быстрая настройка на сервере

Краткая инструкция для настройки системы бэкапов на сервере после развертывания.

## 📋 Предварительные требования

- Приложение развернуто в `/home/ubuntu/penalty-bot` или `/opt/penalty-bot`
- Есть права sudo
- Docker установлен (если используется)

## ⚡ Быстрая настройка (5 минут)

### 1. Переход в директорию проекта

```bash
cd /home/ubuntu/penalty-bot
# или
cd /opt/penalty-bot
```

### 2. Проверка файлов

```bash
# Проверяем наличие скриптов
ls -la scripts/

# Должны быть файлы:
# backup.sh
# backup_docker.sh  
# setup_cron_backup.sh
# restore.sh
```

### 3. Настройка автоматических бэкапов

```bash
# Делаем скрипты исполняемыми
chmod +x scripts/*.sh

# Настраиваем автоматические бэкапы
sudo ./scripts/setup_cron_backup.sh
```

### 4. Создание первого бэкапа

```bash
# Для обычного развертывания
sudo penalty-backup data

# Для Docker-развертывания
sudo ./scripts/backup_docker.sh data
```

### 5. Проверка результата

```bash
# Проверяем статистику
penalty-backup stats

# Проверяем cron задачи
sudo crontab -l | grep backup
```

## 🐳 Для Docker-окружения

Если бот запущен в Docker:

```bash
# Проверяем контейнеры
docker ps

# Используем Docker-скрипт
sudo ./scripts/backup_docker.sh data
sudo ./scripts/backup_docker.sh stats

# Создаем alias для удобства
echo 'alias penalty-backup-docker="sudo /home/ubuntu/penalty-bot/scripts/backup_docker.sh"' >> ~/.bashrc
source ~/.bashrc
```

## 📊 Проверка работы

```bash
# Статистика бэкапов
penalty-backup stats

# Список бэкапов
ls -la /var/backups/penalty-bot/

# Проверка cron
sudo systemctl status cron
sudo tail -f /var/log/cron
```

## 🔧 Команды для управления

```bash
# Создание бэкапов
penalty-backup data      # Данные
penalty-backup full      # Полный
penalty-backup config    # Конфигурация
penalty-backup all       # Все типы
penalty-backup stats     # Статистика

# Восстановление
sudo ./scripts/restore.sh                    # Показать доступные
sudo ./scripts/restore.sh backup-file.tar.gz # Восстановить
```

## 🚨 Устранение проблем

### Проблема: "Приложение не найдено"

```bash
# Проверяем расположение
ls -la bot.py

# Если в другой директории
cd /path/to/penalty-bot
sudo ./scripts/backup.sh data
```

### Проблема: "Permission denied"

```bash
# Проверяем права
chmod +x scripts/backup.sh
sudo ./scripts/backup.sh data
```

### Проблема: "Docker контейнер не найден"

```bash
# Проверяем контейнеры
docker ps

# Используем обычный скрипт
sudo ./scripts/backup.sh data
```

## 📞 Получение помощи

Если что-то не работает:

1. Проверьте, что вы в правильной директории: `pwd`
2. Проверьте наличие файла bot.py: `ls -la bot.py`
3. Проверьте права на скрипты: `ls -la scripts/`
4. Запустите диагностику: `sudo ./scripts/backup.sh stats`

## ✅ Готово!

После выполнения этих шагов:
- ✅ Автоматические бэкапы настроены
- ✅ Команда `penalty-backup` доступна
- ✅ Система готова к работе

**Расписание бэкапов:**
- 🔄 02:00 ежедневно - данные
- 📦 03:00 воскресенье - полный
- ⚙️ 04:00 первое число - конфигурация 