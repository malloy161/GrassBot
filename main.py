import logging
import logging.config
import threading
import time as time_module
import socket
import sys
import gzip
import os
import datetime as dt
from config import LOG_CONFIG, States, LOG_FILE_PATH, TOKEN, ADMIN_ID
from handlers import *
from telegram.ext import (
    Application, CommandHandler, ConversationHandler,
    MessageHandler, filters, PicklePersistence
)
from telegram import Bot, Update
from telegram.error import (Conflict, NetworkError, RetryAfter,
                           TimedOut, BadRequest, Forbidden,
                           ChatMigrated, TelegramError)
import locale
import atexit

# Установка локали
try:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
except locale.Error:
    pass

# Улучшенный обработчик логов
class SafeLogHandler:
    def __init__(self, filename, backup_count=7):
        self.filename = filename
        self.backup_count = backup_count
        self.current_file = None
        self.current_day = dt.datetime.now().strftime("%Y-%m-%d")
        self.lock = threading.Lock()
        self.initialize_logging()

    def initialize_logging(self):
        dirname = os.path.dirname(self.filename)
        if dirname and not os.path.exists(dirname):
            try:
                os.makedirs(dirname, exist_ok=True)
            except Exception as e:
                print(f"Ошибка создания директории логов: {e}")

        logging.config.dictConfig(LOG_CONFIG)
        self.logger = logging.getLogger()

        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                self.logger.removeHandler(handler)

        try:
            self.current_file = open(self.filename, 'a', encoding='utf-8')
            handler = logging.StreamHandler(self.current_file)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(handler)
        except Exception as e:
            print(f"Ошибка открытия файла логов: {e}")
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(console_handler)

        self.monitor_thread = threading.Thread(target=self.log_monitor, daemon=True)
        self.monitor_thread.start()

    def log_monitor(self):
        while True:
            try:
                today = dt.datetime.now().strftime("%Y-%m-%d")
                if today != self.current_day:
                    with self.lock:
                        self.rotate_logs()
                        self.current_day = today
                time_module.sleep(60)
            except Exception as e:
                print(f"Ошибка в мониторе логов: {e}")
                time_module.sleep(300)

    def rotate_logs(self):
        try:
            if self.current_file:
                self.current_file.close()

            if os.path.exists(self.filename):
                new_name = f"{self.filename}.{self.current_day}"

                for _ in range(5):
                    try:
                        os.rename(self.filename, new_name)
                        break
                    except PermissionError:
                        time_module.sleep(1)
                else:
                    print("Не удалось переименовать файл после 5 попыток")
                    return

                self.compress_file(new_name)

            self.current_file = open(self.filename, 'a', encoding='utf-8')

            for handler in self.logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler) and hasattr(handler, 'stream') and handler.stream == self.current_file:
                    self.logger.removeHandler(handler)

            new_handler = logging.StreamHandler(self.current_file)
            new_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(new_handler)

            self.cleanup_old_logs()

        except Exception as e:
            print(f"Ошибка при ротации логов: {e}")
            try:
                self.current_file = open(self.filename, 'a', encoding='utf-8')
            except:
                pass

    def compress_file(self, filename):
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f_in:
                    content = f_in.read()

                with gzip.open(f"{filename}.gz", 'wt', encoding='utf-8') as f_out:
                    f_out.write(content)

                os.remove(filename)
        except Exception as e:
            print(f"Ошибка при сжатии файла {filename}: {e}")

    def cleanup_old_logs(self):
        try:
            log_dir = os.path.dirname(self.filename) or '.'
            files = [f for f in os.listdir(log_dir)
                    if f.startswith(os.path.basename(self.filename)) and f.endswith('.gz')]

            if len(files) > self.backup_count:
                files.sort(key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
                for i in range(len(files) - self.backup_count):
                    os.remove(os.path.join(log_dir, files[i]))
        except Exception as e:
            print(f"Ошибка при очистке старых логов: {e}")

# Инициализация логгера
log_handler = SafeLogHandler(LOG_FILE_PATH, backup_count=7)

def auto_backup():
    backup_logger = logging.getLogger("auto_backup")
    db = SQLiteDatabase()

    while True:
        try:
            users = db.get_all_users()
            if not users:
                backup_logger.info("Нет пользователей для бэкапа")
                time_module.sleep(3600 * 4)
                continue

            backup_logger.info(f"Начато создание бэкапов для {len(users)} пользователей")
            for user_id in users:
                try:
                    db.create_backup(user_id)
                    backup_logger.info(f"Создан бэкап для пользователя {user_id}")
                except Exception as e:
                    backup_logger.error(f"Ошибка при создании бэкапа для {user_id}: {e}")

            time_module.sleep(3600 * 4)
        except Exception as e:
            backup_logger.error(f"Ошибка автоматического бэкапа: {e}")
            time_module.sleep(3600)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик всех ошибок"""
    logger = logging.getLogger(__name__)

    # Обработка специфических ошибок
    if isinstance(context.error, Conflict):
        logger.critical("Конфликт: запущено несколько экземпляров бота! Завершение работы.")
        sys.exit(1)
    elif isinstance(context.error, NetworkError):
        logger.warning("Ошибка сети: %s", context.error)
    elif isinstance(context.error, TimedOut):
        logger.warning("Таймаут соединения: %s", context.error)
    elif isinstance(context.error, RetryAfter):
        logger.warning("Превышен лимит запросов. Ожидаем %s сек.", context.error.retry_after)
    else:
        logger.error("Необработанное исключение: %s", context.error, exc_info=True)

    # Отправка уведомления админу
    try:
        if ADMIN_ID:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ Ошибка бота: {context.error}\n\n"
                     f"Обновление: {update}\n\n"
                     f"Трассировка: {context.error.__traceback__}"
            )
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение об ошибке админу: {e}")

def create_pid_file():
    """Создает PID-файл"""
    pid = os.getpid()
    with open("bot.pid", "w", encoding="utf-8") as f:
        f.write(str(pid))

def remove_pid_file():
    """Удаляет PID-файл"""
    try:
        os.remove("bot.pid")
    except FileNotFoundError:
        pass

async def self_test(bot: Bot):
    """Проверка работоспособности бота"""
    logger = logging.getLogger("self_test")

    try:
        # Проверка соединения с Telegram
        me = await bot.get_me()
        logger.info(f"Self-test: Бот @{me.username} активен")

        # Проверка доставки сообщений
        if ADMIN_ID:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✅ Бот перезапущен и работает\n"
                     f"🆔 ID: {me.id}\n"
                     f"👤 Username: @{me.username}\n"
                     f"🕒 Время сервера: {dt.datetime.now()}"
            )
        return True
    except Exception as e:
        logger.error(f"Self-test failed: {e}")
        if ADMIN_ID:
            try:
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"❌ Ошибка самотестирования бота: {e}"
                )
            except:
                pass
        return False

async def periodic_health_check(bot: Bot, interval=3600):
    """Периодическая проверка здоровья бота"""
    logger = logging.getLogger("health_check")
    while True:
        try:
            await bot.get_me()  # Простая проверка соединения
            logger.debug("Health check: OK")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            if ADMIN_ID:
                try:
                    await bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"⚠️ Проблема с ботом: {e}\n"
                             f"🕒 Время: {dt.datetime.now()}"
                    )
                except:
                    pass
        await asyncio.sleep(interval)

def main() -> None:
    logger = logging.getLogger(__name__)

    # Создаем PID-файл
    create_pid_file()
    atexit.register(remove_pid_file)

    # Проверка блокировки порта
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        lock_socket.bind(("127.0.0.1", 47200))
        logger.info("Проверка блокировки порта: успешно")
    except socket.error:
        logger.critical("Ошибка привязки к порту! Возможно бот уже запущен.")
        sys.exit(1)
    finally:
        lock_socket.close()

    try:
        # Добавляем постоянное хранилище для состояний
        state_file = os.path.abspath('conversation_states.pickle')
        logger.info(f"Используем файл для состояний: {state_file}")
        persistence = PicklePersistence(filepath=state_file)

        application = Application.builder() \
            .token(TOKEN) \
            .persistence(persistence) \
            .build()

        application.add_error_handler(error_handler)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                States.SELECTING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date_selection)],
                States.SELECTING_WORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_work_selection)],
                States.SHOWER_WORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_work)],
                States.MIRROR_WORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_work)],
                States.OTHER_WORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_work)],
                States.ADDITIONAL_SERVICES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_additional)],
                States.MIRROR_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mirror_quantity)],
                States.ADD_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address)],
                States.ADD_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_comment)],
                States.ADD_MORE_WORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_more)],
                States.VIEWING_ENTRIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_view_entries)],
                States.DELETING_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete_entry)],
                States.SETTINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings)],
                States.SETTING_WORK_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_work_days)],
                States.CONFIRM_DELETE_LAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirm_delete_last)],
                States.CONFIRM_DELETE_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirm_delete_entry)]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            name="main_conversation",
            persistent=True,
        )

        application.add_handler(conv_handler)

        # Запускаем бэкапы в отдельном потоке
        backup_thread = threading.Thread(target=auto_backup, daemon=True)
        backup_thread.start()

        # Запускаем самотестирование при старте
        async def post_init(application: Application) -> None:
            bot = application.bot
            success = await self_test(bot)
            if success:
                logger.info("Self-test passed")
            else:
                logger.error("Self-test failed")

            # Запускаем периодическую проверку здоровья
            asyncio.create_task(periodic_health_check(bot))

        application.post_init = post_init

        logger.info("Бот запущен")

        # Запускаем с очисткой обновлений
        application.run_polling(
            drop_pending_updates=True,
            close_loop=False,
            allowed_updates=Update.ALL_TYPES
        )

    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        if ADMIN_ID:
            try:
                bot = Bot(token=TOKEN)
                asyncio.run(bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🔥 Критическая ошибка при запуске бота: {e}"
                ))
            except:
                pass

if __name__ == "__main__":
    # Для Windows устанавливаем политику цикла событий
    if sys.platform == "win32":
        import asyncio
        # Создаем новый цикл событий и устанавливаем его как текущий
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    main()
