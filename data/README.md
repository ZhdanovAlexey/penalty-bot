# Настройка сервисного аккаунта Google API

## Получение файла service_account.json

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. В боковом меню выберите "API и сервисы" > "Учетные данные"
4. Нажмите "Создать учетные данные" > "Ключ сервисного аккаунта"
5. Создайте новый сервисный аккаунт или выберите существующий
6. Выберите роль "Редактор" (Editor) или "Просмотрщик" (Viewer)
7. Нажмите "Создать" и скачайте файл JSON
8. Переименуйте скачанный файл в `service_account.json` и поместите его в эту директорию (`data/`)

## Содержимое файла service_account.json

Файл должен содержать примерно следующие поля:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n.....\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
  "client_id": "client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
}
```

## Предоставление доступа к таблице

1. После создания сервисного аккаунта, скопируйте email из поля `client_email`
2. Откройте вашу Google таблицу
3. Нажмите кнопку "Поделиться" в правом верхнем углу
4. Вставьте email сервисного аккаунта и предоставьте доступ "Редактор" или "Просмотрщик"
5. Нажмите "Готово"

## Включение Google Sheets API

1. В Google Cloud Console выберите ваш проект
2. Перейдите в "API и сервисы" > "Библиотека"
3. Найдите "Google Sheets API" и включите его для вашего проекта

## Получение ID таблицы

ID таблицы - это часть URL между /d/ и /edit в ссылке на вашу таблицу:
```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

Скопируйте этот ID и добавьте его в файл `.env` как значение переменной `SPREADSHEET_ID`. 