# Grass Bot - Краткий обзор

Telegram бот для учета выполненных работ с функциями отчетности и напоминаний.

## Основные возможности
- 📝 «Учет работ»: душевые кабины, зеркала, другие работы
- 📊 «Отчеты»: автоматическая генерация Excel-файлов
- 🔔 «Напоминания»: ежедневные уведомления
- ⚙️ «Настройки»: рабочие дни, отпускной режим
- 📋 «Управление»: просмотр, редактирование и удаление записей

## Быстрый старт
1. Установите зависимости:

pip install python-telegram-bot pytz openpyxl python-dotenv

2. Создайте «.env» файл:

TELEGRAM_BOT_TOKEN=ваш_токен_бота

3. Запустите бота:
   
python main.py

## Команды бота
- /start - главное меню
- «Душевые/Зеркала/Другая работа» - добавление работ
- «Выгрузить отчет» - получение Excel-отчета
- «Удалить последнюю» - удаление последней записи
- «Статистика» - просмотр статистики
- «Настройки» - конфигурация бота

## Структура проекта
├── main.py         # Запуск бота и управление процессами
├── handlers.py     # Обработчики сообщений и команд
├── database.py     # Работа с SQLite базой данных
├── keyboards.py    # Генерация клавиатур
├── config.py       # Конфигурационные параметры
└── .env            # Переменные окружения

> Бот поддерживает многопоточность, автоматические бэкапы и обработку ошибок с уведомлением администратора.



# Grass Bot - English Version

A Telegram bot for tracking completed work activities with reporting and reminder features.

## Core Features
- 📝 «Work logging»: Shower cabins, mirrors, and other custom work
- 📊 «Reporting»: Automatic Excel report generation
- 🔔 «Reminders»: Daily notifications to log activities
- ⚙️ «Customization»: Work day schedules, vacation mode
- 📋 «Management»: View, edit, and delete entries

## Quick Setup
1. Install dependencies:

pip install python-telegram-bot pytz openpyxl python-dotenv

2. Create «.env» file:

TELEGRAM_BOT_TOKEN=your_bot_token_here

3. Start the bot:

python main.py

## Bot Commands
- /start - Main menu
- «Showers/Mirrors/Other work» - Add work entries
- «Generate report» - Get Excel report
- «Delete last» - Remove last entry
- «Statistics» - View work statistics
- «Settings» - Configure bot preferences

## Project Structure
├── main.py         # Bot startup and core processes
├── handlers.py     # Message and command processors
├── database.py     # SQLite database operations
├── keyboards.py    # Interactive keyboards
├── config.py       # Configuration settings
└── .env            # Environment variables

## Technical Highlights
- «Multithreading»: Safe database operations and background tasks
- «Automatic backups»: Daily data backups
- «Error handling»: Comprehensive logging and admin notifications
- «Caching»: Optimized performance for frequent operations
- «Timezone support»: Moscow time (configurable)

Start using the bot by sending «/start» in Telegram after launching the application.
