import sqlite3
import os
from typing import List, Dict, Any, Optional

# Путь к файлу базы данных
DB_PATH = "data/bot_database.sqlite"

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # Инициализируем соединение и создаем таблицы, если их нет
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()
    
    def create_tables(self):
        """Создает необходимые таблицы в базе данных"""
        cursor = self.conn.cursor()
        
        # Таблица для хранения информации о подписанных пользователях
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribed_users (
            user_id INTEGER PRIMARY KEY,
            is_subscribed INTEGER DEFAULT 1,  -- 1 = подписан, 0 = не подписан
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Таблица для хранения истории расчетов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            contract_amount REAL,
            deadline_date TEXT,
            calculation_date TEXT,
            is_individual INTEGER,  -- 1 = физлицо, 0 = юрлицо
            is_unique INTEGER,      -- 1 = уникальный, 0 = не уникальный
            penalty_amount REAL,
            delay_days INTEGER,
            moratorium_days INTEGER,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES subscribed_users (user_id)
        )
        ''')
        
        self.conn.commit()
    
    def add_subscribed_user(self, user_id: int, first_name: str = None, last_name: str = None, username: str = None, is_subscribed: bool = True) -> bool:
        """
        Добавляет пользователя в базу данных подписчиков
        
        Args:
            user_id: ID пользователя Telegram
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            username: Username пользователя
            is_subscribed: Статус подписки (True - подписан, False - не подписан)
            
        Returns:
            True, если пользователь успешно добавлен, иначе False
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO subscribed_users (user_id, first_name, last_name, username, is_subscribed)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, first_name, last_name, username, 1 if is_subscribed else 0)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при добавлении пользователя {user_id} в базу данных: {e}")
            return False
    
    def remove_subscribed_user(self, user_id: int) -> bool:
        """
        Отмечает пользователя как неподписанного
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            True, если пользователь успешно обновлен, иначе False
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE subscribed_users SET is_subscribed = 0
                WHERE user_id = ?
                """,
                (user_id,)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при удалении пользователя {user_id} из базы данных: {e}")
            return False
    
    def is_user_subscribed(self, user_id: int) -> bool:
        """
        Проверяет, подписан ли пользователь
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            True, если пользователь подписан, иначе False
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT is_subscribed FROM subscribed_users
                WHERE user_id = ?
                """,
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result is None:
                return False
                
            return bool(result[0])
        except Exception as e:
            print(f"Ошибка при проверке подписки пользователя {user_id}: {e}")
            return False
    
    def save_calculation(self, user_id: int, data: Dict[str, Any]) -> bool:
        """
        Сохраняет результаты расчета в базу данных
        
        Args:
            user_id: ID пользователя Telegram
            data: Данные расчета
            
        Returns:
            True, если расчет успешно сохранен, иначе False
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO calculations (
                    user_id, contract_amount, deadline_date, calculation_date,
                    is_individual, is_unique, penalty_amount, delay_days, moratorium_days
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    data.get("contract_amount", 0),
                    data.get("deadline_date_str", ""),
                    data.get("calculation_date_str", ""),
                    1 if data.get("is_individual", True) else 0,
                    1 if data.get("is_unique", False) else 0,
                    data.get("penalty_amount", 0),
                    data.get("delay_days", 0),
                    data.get("moratorium_days", 0)
                )
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при сохранении расчета для пользователя {user_id}: {e}")
            return False
    
    def get_total_users_count(self) -> int:
        """
        Получает общее количество пользователей в базе данных
        
        Returns:
            Количество пользователей
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM subscribed_users")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Ошибка при получении количества пользователей: {e}")
            return 0
    
    def get_subscribed_users_count(self) -> int:
        """
        Получает количество подписанных пользователей
        
        Returns:
            Количество подписанных пользователей
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM subscribed_users WHERE is_subscribed = 1")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Ошибка при получении количества подписанных пользователей: {e}")
            return 0
    
    def get_total_calculations_count(self) -> int:
        """
        Получает общее количество расчетов в базе данных
        
        Returns:
            Количество расчетов
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM calculations")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Ошибка при получении количества расчетов: {e}")
            return 0
    
    def get_calculations_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получает историю расчетов для конкретного пользователя
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Список расчетов пользователя
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM calculations
                WHERE user_id = ?
                ORDER BY calculated_at DESC
                """,
                (user_id,)
            )
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
                
            return results
        except Exception as e:
            print(f"Ошибка при получении расчетов пользователя {user_id}: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получает общую статистику использования бота
        
        Returns:
            Словарь с различными статистическими данными
        """
        stats = {
            "total_users": self.get_total_users_count(),
            "subscribed_users": self.get_subscribed_users_count(),
            "total_calculations": self.get_total_calculations_count(),
        }
        
        try:
            cursor = self.conn.cursor()
            
            # Средняя сумма неустойки
            cursor.execute("SELECT AVG(penalty_amount) FROM calculations")
            stats["avg_penalty"] = cursor.fetchone()[0] or 0
            
            # Средняя сумма договора
            cursor.execute("SELECT AVG(contract_amount) FROM calculations")
            stats["avg_contract_amount"] = cursor.fetchone()[0] or 0
            
            # Количество расчетов для физических лиц
            cursor.execute("SELECT COUNT(*) FROM calculations WHERE is_individual = 1")
            stats["individual_calculations"] = cursor.fetchone()[0] or 0
            
            # Количество расчетов для юридических лиц
            cursor.execute("SELECT COUNT(*) FROM calculations WHERE is_individual = 0")
            stats["legal_calculations"] = cursor.fetchone()[0] or 0
            
            # Количество расчетов для уникальных объектов
            cursor.execute("SELECT COUNT(*) FROM calculations WHERE is_unique = 1")
            stats["unique_objects_calculations"] = cursor.fetchone()[0] or 0
            
            return stats
        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            return stats
    
    def close(self):
        """Закрывает соединение с базой данных"""
        if self.conn:
            self.conn.close()
            
# Create a global instance of the database
db = Database() 