import os
import pytz
from dotenv import load_dotenv
from datetime import time
from enum import IntEnum
import logging

# Определяем базовую директорию
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env или переменных окружения")

# Добавлен ADMIN_ID для уведомлений
ADMIN_ID = os.getenv("ADMIN_ID")
if ADMIN_ID:
    try:
        ADMIN_ID = int(ADMIN_ID)  # Конвертируем в число
    except ValueError:
        ADMIN_ID = None
        logging.warning("ADMIN_ID должен быть числовым значением")
else:
    ADMIN_ID = None

MOSCOW_TZ = pytz.timezone('Europe/Moscow')

MONTHS_GENITIVE = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}

DAYS_MAP = {"Пн": 0, "Вт": 1, "Ср": 2, "Чт": 3, "Пт": 4, "Сб": 5, "Вс": 6}
DAYS_NAMES = list(DAYS_MAP.keys())

class States(IntEnum):
    SELECTING_DATE = 0
    SELECTING_WORK = 1
    ADD_COMMENT = 2
    SHOWER_WORK = 3
    MIRROR_WORK = 4
    OTHER_WORK = 5
    ADDITIONAL_SERVICES = 6
    ADD_ADDRESS = 7
    ADD_MORE_WORK = 8
    VIEWING_ENTRIES = 9
    DELETING_ENTRY = 10
    MIRROR_QUANTITY = 11
    SETTINGS = 12
    SETTING_WORK_DAYS = 13
    CONFIRM_DELETE_LAST = 14
    CONFIRM_DELETE_ENTRY = 15

DEFAULT_SETTINGS = {
    "reminders": True,
    "work_days": [0, 1, 2, 3, 4],
    "vacation_mode": False
}

REMINDER_TIME = time(14, 0)

# Абсолютные пути к файлам
LOG_FILE_PATH = os.path.join(BASE_DIR, "bot.log")
DB_FILE_PATH = os.path.join(BASE_DIR, "bot_data.db")
PID_FILE_PATH = os.path.join(BASE_DIR, "bot.pid")

# Конфигурация логгера
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "WARNING",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_FILE_PATH,
            "encoding": "utf-8",
            "formatter": "verbose",
            "level": "INFO"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        },
        "httpx": {
            "level": "WARNING",
            "propagate": False
        },
        "apscheduler": {
            "level": "WARNING",
            "propagate": False
        },
        "telegram": {
            "level": "WARNING",
            "propagate": False
        }
    }
}
