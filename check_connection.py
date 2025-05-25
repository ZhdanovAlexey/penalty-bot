import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Проверяем наличие необходимых переменных окружения
required_env_vars = ['BOT_TOKEN', 'SPREADSHEET_ID']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ Отсутствуют необходимые переменные окружения: {', '.join(missing_vars)}")
    print("Убедитесь, что вы создали файл .env на основе .env.example и заполнили все необходимые переменные.")
    sys.exit(1)

# Проверяем наличие файла service_account.json
if not os.path.exists('data/service_account.json'):
    print("❌ Файл service_account.json не найден в директории data/")
    print("Следуйте инструкциям в файле data/README.md для создания сервисного аккаунта и получения JSON файла.")
    sys.exit(1)

print("✅ Проверка переменных окружения и наличия файла service_account.json пройдена успешно")

# Пробуем импортировать необходимые библиотеки
try:
    from services.sheets import GoogleSheetsService
    from services.calculator import PenaltyCalculator
    print("✅ Необходимые библиотеки импортированы успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что вы установили все зависимости: pip install -r requirements.txt")
    sys.exit(1)

# Проверяем подключение к Google Sheets
print("\nПроверка подключения к Google Sheets...")
try:
    service = GoogleSheetsService()
    data = service.get_rates_and_moratoriums()
    
    if not data:
        print("⚠️ Данные получены, но таблица пуста или не содержит правильно отформатированных данных.")
        print("Убедитесь, что ваша Google таблица содержит данные в правильном формате.")
        print("В папке data/example_data.csv есть пример данных, который можно импортировать в Google Sheets.")
    else:
        print(f"✅ Успешно получено {len(data)} строк данных из таблицы")
        print(f"   Первая запись: Дата {data[0]['date']}, Ставка {data[0]['rate']*100}%, Мораторий: {'Да' if data[0]['moratorium'] else 'Нет'}")
        print(f"   Последняя запись: Дата {data[-1]['date']}, Ставка {data[-1]['rate']*100}%, Мораторий: {'Да' if data[-1]['moratorium'] else 'Нет'}")
    
    print("\n✅ Проверка подключения к Google Sheets успешно завершена!")
    print("Теперь вы можете запустить бота командой: python bot.py")
    
except Exception as e:
    print(f"❌ Ошибка при подключении к Google Sheets: {e}")
    print("Проверьте инструкции в файле data/README.md для правильной настройки сервисного аккаунта и доступа к таблице.")
    sys.exit(1) 