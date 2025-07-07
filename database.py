import sqlite3
import json
import threading
import logging
import time
import re
import calendar
from contextlib import closing
from functools import lru_cache
from config import DEFAULT_SETTINGS, MOSCOW_TZ, States

logger = logging.getLogger(__name__)

class SQLiteDatabase:
    """Класс для работы с базой данных SQLite с поддержкой многопоточности"""
    def __init__(self, db_name="bot_data.db"):
        self.db_name = db_name
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        try:
            with self.lock, closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                # Таблица записей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        date TEXT NOT NULL,
                        works TEXT NOT NULL,
                        address TEXT,
                        comment TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Таблица настроек
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        user_id TEXT PRIMARY KEY,
                        reminders BOOLEAN DEFAULT 1,
                        work_days TEXT NOT NULL,
                        vacation_mode BOOLEAN DEFAULT 0
                    )
                """)

                # Таблица бэкапов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS backups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        backup_data TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Оптимизированные индексы
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_user_date ON entries(user_id, date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_user_id ON entries(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_backups_user_id ON backups(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_backups_timestamp ON backups(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_user_id ON settings(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_reminders ON settings(reminders)")

                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")

    def _get_connection(self):
        return sqlite3.connect(self.db_name, isolation_level=None, check_same_thread=False)

    @lru_cache(maxsize=128)
    def get_settings(self, user_id: str) -> dict:
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT reminders, work_days, vacation_mode FROM settings WHERE user_id = ?",
                    (user_id,)
                )
                row = cursor.fetchone()
                return {
                    "reminders": bool(row[0]),
                    "work_days": json.loads(row[1]),
                    "vacation_mode": bool(row[2])
                } if row else DEFAULT_SETTINGS.copy()
        except Exception as e:
            logger.error(f"Ошибка получения настроек: {e}")
            return DEFAULT_SETTINGS.copy()

    def save_settings(self, user_id: str, settings: dict):
        try:
            with self.lock, closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO settings
                    (user_id, reminders, work_days, vacation_mode)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        int(settings["reminders"]),
                        json.dumps(settings["work_days"]),
                        int(settings["vacation_mode"])
                    )
                )
                conn.commit()
                self.get_settings.cache_clear()
        except sqlite3.Error as e:
            logger.error(f"Ошибка сохранения настроек: {e}")

    def add_entry(self, user_id: str, entry: dict) -> int:
        try:
            with self.lock, closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO entries
                    (user_id, date, works, address, comment)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        entry["date"],
                        json.dumps(entry["works"]),
                        entry.get("address", ""),
                        entry.get("comment", "")
                    )
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Ошибка добавления записи: {e}")
            return None

    def get_entries(self, user_id: str, date_range: tuple = None) -> list:
        """Получение записей пользователя за период"""
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                query = "SELECT id, date, works, address, comment FROM entries WHERE user_id = ?"
                params = [user_id]

                if date_range:
                    query += " AND date BETWEEN ? AND ?"
                    params.extend(date_range)

                query += " ORDER BY date DESC"
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()

                entries = []
                for row in rows:
                    entry = {
                        "id": row[0],
                        "date": row[1],
                        "works": json.loads(row[2]),
                        "address": row[3],
                        "comment": row[4]
                    }
                    entries.append(entry)
                return entries
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения записей: {e}")
            return []

    def get_last_entry(self, user_id: str) -> dict:
        """Получение последней записи пользователя"""
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, date, works, address, comment
                    FROM entries
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (user_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "date": row[1],
                        "works": json.loads(row[2]),
                        "address": row[3],
                        "comment": row[4]
                    }
                return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения последней записи: {e}")
            return None

    def delete_entry(self, entry_id: int, user_id: str) -> bool:
        """Удаление записи по ID и user_id (для безопасности)"""
        try:
            with self.lock, closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM entries WHERE id = ? AND user_id = ?",
                    (entry_id, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления записи: {e}")
            return False

    def get_all_users(self) -> list:
        """Получение списка всех пользователей, у которых есть записи"""
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT user_id FROM entries")
                rows = cursor.fetchall()
                return [row[0] for row in rows] if rows else []
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return []

    def create_backup(self, user_id: str):
        """Создание бэкапа данных пользователя"""
        try:
            entries = self.get_entries(user_id)
            if not entries:
                logger.info(f"Нет записей для пользователя {user_id} при создании бэкапа")
                return

            backup_data = json.dumps(entries)
            with self.lock, closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO backups (user_id, backup_data) VALUES (?, ?)",
                    (user_id, backup_data)
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания бэкапа для {user_id}: {e}")

class StatsCache:
    """Кэш статистики с TTL и автоматической очисткой"""
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl  # 1 час
        self.last_clean = time.time()

    def get(self, user_id: str, calculate_func):
        now = time.time()
        # Автоочистка каждые 10 минут
        if now - self.last_clean > 600:
            self.clean_cache()
            self.last_clean = now

        if user_id in self.cache:
            cached = self.cache[user_id]
            if now - cached["timestamp"] < self.ttl:
                return cached["data"]

        stats = calculate_func(user_id)
        self.cache[user_id] = {"data": stats, "timestamp": now}
        return stats

    def clean_cache(self):
        now = time.time()
        expired_users = [
            user_id for user_id, data in self.cache.items()
            if now - data["timestamp"] > self.ttl
        ]
        for user_id in expired_users:
            del self.cache[user_id]

    def invalidate(self, user_id: str = None):
        if user_id:
            if user_id in self.cache:
                del self.cache[user_id]
        else:
            self.cache.clear()
