from telegram import ReplyKeyboardMarkup
from config import DAYS_NAMES, DAYS_MAP

def create_keyboard(buttons, add_back=True, row_width=2):
    """Создание клавиатуры из списка кнопок"""
    if not isinstance(buttons, list):
        buttons = list(buttons)

    # Создание строк клавиатуры
    rows = []
    for i in range(0, len(buttons), row_width):
        rows.append(buttons[i:i+row_width])

    if add_back and "Назад" not in buttons:
        rows.append(["Назад"])

    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

def main_keyboard():
    """Главное меню"""
    buttons = [
        "Душевые", "Зеркала", "Другая работа",
        "Выгрузить отчет", "Удалить последнюю", "Просмотреть работы",
        "Статистика", "⚙️ Настройки"
    ]
    return create_keyboard(buttons, add_back=False, row_width=3)

def work_keyboard(work_type, group_started=False):
    """Клавиатура для выбора типа работы"""
    buttons = {
        "shower": [
            "Угловая распашка", "Прямая распашка", "Угловая откадка",
            "Шторка на ванную", "Фикс на ванную", "Фикс в душ",
            "Фикс до потолка", "Трапеция", "Полутрапеция",
            "Добавить за прошлую дату"
        ],
        "mirror": [
            "Обычное с подсветкой", "Большое с подсветкой",
            "В сборной раме", "Зеркало клей",
            "Навес", 
            "Добавить за прошлую дату"
        ],
        "other": ["Ввести работу вручную", "Добавить за прошлую дату"]
    }
    kb_buttons = buttons.get(work_type, [])
    return create_keyboard(kb_buttons, row_width=2)

def mirror_quantity_keyboard():
    """Клавиатура для выбора количества зеркал"""
    return create_keyboard(["1", "2", "3", "4", "5", "6", "Пропустить"], row_width=3)

def additional_services_keyboard():
    """Клавиатура дополнительных услуг"""
    return create_keyboard(["1 полочка", "2 полочки", "3 полочки", "Гидрофобное", "Пропустить"], row_width=2)

def date_selection_keyboard():
    """Клавиатура выбора даты"""
    buttons = [
        "Сегодня", "Вчера", "Позавчера",
        "Текущий месяц", "Предыдущий месяц", "Отмена"
    ]
    return create_keyboard(buttons, add_back=False, row_width=2)

def add_more_keyboard():
    """Клавиатура добавления работ"""
    return create_keyboard(["Добавить еще работу", "Завершить"], add_back=False, row_width=1)

def view_entries_keyboard():
    """Клавиатура просмотра записей"""
    return create_keyboard(["Удалить запись", "Назад"], add_back=False)

def settings_keyboard():
    """Клавиатура настроек"""
    return create_keyboard(["⏰ Напоминания Вкл/Выкл", "📅 Рабочие дни", "🏖 Режим отпуска", "Назад"], add_back=False)

def confirm_keyboard():
    """Клавиатура подтверждения действий"""
    return create_keyboard(["✅ Да, удалить", "❌ Нет, отменить"], add_back=False, row_width=2)

def work_days_keyboard(work_days):
    """Клавиатура для выбора рабочих дней"""
    keyboard = []
    row = []
    for day_name in DAYS_NAMES:
        prefix = "✅ " if DAYS_MAP[day_name] in work_days else "❌ "
        row.append(f"{prefix}{day_name}")
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append(["Готово"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
