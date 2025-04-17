import os
import sys
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from bot_functions import (
    create_table, save_chat_id, get_all_chat_ids, save_user_question,
    get_all_user_questions, get_available_accounts_from_sheet,
    process_account_request, RestartOnChange
)

# Вставьте токен от BotFather
TOKEN = os.getenv('7393240724:AAGS92BpB2TD1Vdu48cXmpHXbbuWPbFgqSM', 'YOUR_BOT_TOKEN')

# Chat ID пользователя, которому разрешено отправлять сообщения
ALLOWED_USER_ID = int(os.getenv('1953618185', 'YOUR_USER_ID'))

# Путь к вашему файлу учетных данных
#CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', '/path/to/your/credentials.json')

# Функция для отправки сообщения всем пользователям
async def broadcast_message(context: ContextTypes, message: str):
    chat_ids = get_all_chat_ids()
    for chat_id in chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")

# Функция для получения chat ID пользователя
async def get_chat_id(update: Update, context: ContextTypes) -> None:
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Ваш Chat ID: {chat_id}")

# Функция для главного меню
async def start(update: Update, context: ContextTypes) -> None:
    save_chat_id(update.effective_chat.id)
    welcome_message = "       МЕНЮ       "
    keyboard = [
        [InlineKeyboardButton("Методичка", callback_data='guide')],
        [InlineKeyboardButton("Магазин FB аккаунтов", callback_data='fb_store')],
        [InlineKeyboardButton("Купить Прокси", callback_data='buy_proxy')],
        [InlineKeyboardButton("Связка для залива и заработка $", callback_data='earn_money')],
        [InlineKeyboardButton("FAQ", callback_data='faq')]
    ]
    if update.effective_chat.id == ALLOWED_USER_ID:
        keyboard.append([InlineKeyboardButton("Админ панель", callback_data='admin_panel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_message, reply_markup=reply_markup)

# Функция обработки нажатия кнопок
async def button(update: Update, context: ContextTypes) -> None:
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass
    await handle_button_press(update, context, query.data)

# Обработка нажатия кнопок
async def handle_button_press(update: Update, context: ContextTypes, button_data: str) -> None:
    query = update.callback_query
    if button_data == 'broadcast' and query.from_user.id != ALLOWED_USER_ID:
        await query.edit_message_text(text="У вас нет доступа к этой функции.")
        return
    if button_data == 'guide':
        await show_guide(update, context)
    elif button_data == 'fb_store':
        await show_fb_store(update, context)
    elif button_data == 'buy_proxy':
        await query.edit_message_text(text="Тут вы сможете купить прокси, но позже.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в меню", callback_data='back_main')]]))
    elif button_data == 'earn_money':
        await query.edit_message_text(text="Связка еще тестируется, зайдите сюда позже.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в меню", callback_data='back_main')]]))
    elif button_data == 'faq':
        await query.edit_message_text(text="Введите ваш вопрос:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data='back_main')]]))
        context.user_data['waiting_for_question'] = True
    elif button_data == 'admin_panel':
        await show_admin_panel(update, context)
    elif button_data == 'part1':
        await show_part1(update, context)
    elif button_data == 'step1':
        await show_step1(update, context)
    elif button_data == 'step2':
        await show_step2(update, context)
    elif button_data == 'step3':
        await show_step3(update, context)
    elif button_data == 'part2':
        await show_part2(update, context)
    elif button_data == 'part3':
        await show_part3(update, context)
    elif button_data == 'part4':
        await show_part4(update, context)
    elif button_data == 'part5':
        await show_part5(update, context)
    elif button_data in ['step4', 'step5', 'step6', 'step7', 'step8', 'step9', 'step10', 'step11', 'step12', 'step13', 'step14', 'step15', 'step16', 'step17', 'step18', 'step19', 'step20', 'step21', 'step22', 'step23', 'step24', 'step25', 'step26', 'step27', 'step28', 'step29', 'step30', 'step31', 'step32', 'step33', 'step34', 'step35', 'step36']:
        await show_step_part4(update, context, button_data)
    elif button_data == 'broadcast':
        await query.message.reply_text("Введите сообщение, которое хотите отправить всем пользователям:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data='admin_panel')]]))
        context.user_data['waiting_for_broadcast'] = True
    elif button_data == 'user_stats':
        await show_user_stats(update, context)
    elif button_data == 'user_questions':
        await show_user_questions(update, context)
    elif button_data.startswith('answer_'):
        await handle_answer_button(update, context, button_data)
    elif button_data == 'back_main':
        await start(update, context)
    elif button_data.startswith('get_accounts_'):
        try:
            parts = button_data.split('_')
            if len(parts) != 3:
                raise ValueError("Неверный формат данных.")
            _, product_id, quantity = parts
            quantity = int(quantity)
            await process_account_request(update, context, CREDENTIALS_FILE, product_id, quantity)
        except ValueError:
            await query.message.reply_text("Ошибка при обработке запроса. Пожалуйста, попробуйте еще раз.")
    elif button_data == 'fb_king_farm':
        await handle_fb_king_farm(update, context)

# Функция для обработки ввода сообщения для рассылки
async def handle_message(update: Update, context: ContextTypes) -> None:
    if context.user_data.get('waiting_for_broadcast'):
        message_text = update.message.text
        await broadcast_message(context, message_text)
        context.user_data['waiting_for_broadcast'] = False
        await update.message.reply_text("Сообщение успешно отправлено всем пользователям!")
    elif context.user_data.get('waiting_for_question'):
        chat_id = update.effective_chat.id
        question_text = update.message.text
        save_user_question(chat_id, question_text)
        context.user_data['waiting_for_question'] = False
        await update.message.reply_text("Ваш вопрос отправлен. Мы свяжемся с вами в ближайшее время.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в меню", callback_data='back_main')]]))
    elif context.user_data.get('waiting_for_answer'):
        question_id = context.user_data['current_question_id']
        answer_text = update.message.text
        context.user_data['waiting_for_answer'] = False
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT chat_id, question_text FROM user_questions WHERE id = ?', (question_id,))
            chat_id, question_text = cursor.fetchone()
        response_text = (
            f"Вы отправили запрос: {question_text}\n"
            f"Ответ команды: {answer_text}"
        )
        await context.bot.send_message(chat_id=chat_id, text=response_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад в меню", callback_data='back_main')]]))
        await update.message.reply_text("Ответ отправлен пользователю.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад к Запросам", callback_data='user_questions')]]))
    elif context.user_data.get('waiting_for_fb_quantity'):
        await handle_fb_quantity_input(update, context)

# Функция для отображения магазина FB аккаунтов
async def show_fb_store(update: Update, context: ContextTypes) -> None:
    await update.callback_query.message.edit_text(
        "Аккаунты фармятся, ожидайте...",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад в меню", callback_data='back_main')]])
    )
    await asyncio.sleep(2)

# Функция для обработки нажатия кнопки "fb_king_farm"
async def handle_fb_king_farm(update: Update, context: ContextTypes):
    available_accounts = get_available_accounts_from_sheet(CREDENTIALS_FILE)
    available_count = available_accounts['king_farm']
    await update.callback_query.edit_message_text(
        f"В наличии: {available_count}\n"
        "Введите количество, которое хотите купить:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='fb_store')]])
    )
    context.user_data['current_product'] = 'king_farm'
    context.user_data['waiting_for_fb_quantity'] = True

# Функция для обработки ввода количества аккаунтов
async def handle_fb_quantity_input(update: Update, context: ContextTypes):
    try:
        quantity = int(update.message.text)
        product_info = {
            'king_farm': {
                'name': 'UA КИНГ Фарм 30+ дней 15$',
                'price': 15
            }
        }
        product = product_info[context.user_data['current_product']]
        total_price = quantity * product['price']
        await update.message.reply_text(
            f"Вы покупаете: {product['name']}\n"
            f"Количество: {quantity}\n"
            f"На Сумму: {total_price}$",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Получить Аккаунты", callback_data=f'get_accounts_{context.user_data["current_product"]}_{quantity}'),
                InlineKeyboardButton("Назад", callback_data='fb_king_farm')
            ]])
        )
        context.user_data['waiting_for_fb_quantity'] = False
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='fb_king_farm')]]))

# Функция для отображения методички с новым разделом
async def show_guide(update: Update, context: ContextTypes):
    guide_buttons = [
        [InlineKeyboardButton("Блок 1. Установка антидетект браузера AdsPower", callback_data='part1')],
        [InlineKeyboardButton("Блок 2. Добавление Прокси в AdsPower", callback_data='part2')],
        [InlineKeyboardButton("Блок 3. Добавление аккаунта в AdsPower", callback_data='part3')],
        [InlineKeyboardButton("Блок 4. Прогрев ФП и Привязка карты", callback_data='part4')],
        [InlineKeyboardButton("Блок 5. Трекер Keitaro", callback_data='part5')],
        [InlineKeyboardButton("Вернуться в меню", callback_data='back_main')]
    ]
    reply_markup = InlineKeyboardMarkup(guide_buttons)
    await update.callback_query.message.edit_text(text="Выберите часть методички:", reply_markup=reply_markup)

# Функция для отображения части 4 методички
async def show_part4(update: Update, context: ContextTypes):
    steps_buttons = []
    for i in range(1, 24):
        if (i - 1) % 3 == 0:
            steps_buttons.append([])
        steps_buttons[-1].append(InlineKeyboardButton(f"Шаг {i}", callback_data=f'step{i + 13}'))
    steps_buttons.append([InlineKeyboardButton("Вернуться к методичке", callback_data='guide')])
    reply_markup = InlineKeyboardMarkup(steps_buttons)
    await update.callback_query.message.edit_text(text="**Прогрев ФП и Привязка карты**\n\nВыберите шаг:", reply_markup=reply_markup)

# Функция для отображения части 5 методички
async def show_part5(update: Update, context: ContextTypes):
    message_text = (
        "Получаем доступ к трекеру Keitaro, для этого переходим по ссылке [Keitaro](https://keitaro.io/en/), "
        "регистрируемся, оплачиваем пакет, который нам подходит (выделен зеленым), "
        "и докупаем сервер для Keitaro. По точности настроек обращаемся в Библиотеку Keitaro, "
        "ссылка конечно тут: [Документация Keitaro](https://docs.keitaro.io/ru/get-started/auto-installation.html)."
    )
    keyboard = [
        [InlineKeyboardButton("Предыдущий шаг", callback_data='step36')],
        [InlineKeyboardButton("Следующий шаг", callback_data='none')],
        [InlineKeyboardButton("Вернуться к методичке", callback_data='guide')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(text=message_text, parse_mode="Markdown", reply_markup=reply_markup)

# Обновление функции show_step_part4 для навигации между шагами
async def show_step_part4(update: Update, context: ContextTypes, step_data: str):
    steps = {
        'step14': ("Шаг 1", "Переключаемся на ФП", "https://prnt.sc/ngKCg9IX1HGb"),
        'step15': ("Шаг 2", "Переходим на главную страницу", "https://prnt.sc/3Q42Z7W5bMAd"),
        'step16': ("Шаг 3", "Жмем разместить рекламу", "https://prnt.sc/emOmxvmKE4kz"),
        'step17': ("Шаг 4", "Нажимаем создать рекламу", "https://prnt.sc/cgZMXE43bAjk"),
        'step18': ("Шаг 5", "Нажимаем начать", "https://prnt.sc/aGh79zPvU9_G"),
        'step19': ("Шаг 6", "Нажимаем Начало работы с автоматизированной рекламой", "https://prnt.sc/-8Z2FmqM2jlQ"),
        'step20': ("Шаг 7", "Выбираем Нет", "https://prnt.sc/nS-xPO7I9HSZ"),
        'step21': ("Шаг 8", "Выбираем Нет", "https://prnt.sc/MSbspags3O7G"),
        'step22': ("Шаг 9", "Выбираем Нет", "https://prnt.sc/CkIM_qomoK-C"),
        'step23': ("Шаг 10", "Выбираем Нет", "https://prnt.sc/rmfTnu0E6dxH"),
        'step24': ("Шаг 11", "В данном поле вводим название страны на которое будет пролив рекламы", "https://prnt.sc/D_TCFTutJN1a"),
        'step25': ("Шаг 12", "Тут пропускаем и ничего не вводим", "https://prnt.sc/QKSUtCsbOo21"),
        'step26': ("Шаг 13", "Так же пропускаем этот пункт и жмем Далее", "https://prnt.sc/VVQj2fKVm0sH"),
        'step27': ("Шаг 14", "Начинаем привязывать карту", "https://prnt.sc/v8wKx-f0Z9O3"),
        'step28': ("Шаг 15", "Проверяем чтобы валюта и часовой пояс совпадали с ГЕО вашего открута (В нашем случае это Украина)", "https://prnt.sc/zGOHGZtLAOG0"),
        'step29': ("Шаг 16", "Выбираем Дебитовая или кредитная карта и ждем Далее", "https://prnt.sc/Igcw40P2Ip16"),
        'step30': ("Шаг 17", "Вводим данные карты которую планируете привязать", "https://prnt.sc/TldEuPjh0tKU"),
        'step31': ("Шаг 18", "Всегда выбираем второй пункт и нажимаем Сохранить", "https://prnt.sc/Cdrv_U6H8fwz"),
        'step32': ("Шаг 19", "Нажимаем разместить", "https://prnt.sc/AUnnEwPE29WA"),
        'step33': ("Шаг 20", "Нажимаем Перейти в центр рекламы", "https://prnt.sc/I5ki-WKgxWhQ"),
        'step34': ("Шаг 21", "Нажимаем на Ads Manager как показывает стрелочка", "https://prnt.sc/MgeIwDW1Dhv0"),
        'step35': ("Шаг 22", "Если сделали все правильно, то в Ads у вас появится объявление, ждем пока появится статус Действующая, и отключаем его", "https://prnt.sc/Sx17Gw33pvtH"),
        'step36': ("Шаг 23", "Мои поздравления ФП прогрето, и карта без рисков привязана", "")
    }
    step_title, step_text, image_url = steps[step_data]
    await update.callback_query.message.reply_photo(photo=image_url, caption=f"{step_title}\n{step_text}", parse_mode="Markdown")
    step_number = int(step_data[-2:])
    keyboard = [
        [
            InlineKeyboardButton("Предыдущий шаг" if step_number > 14 else "Вернуться к методичке", callback_data=f'step{step_number - 1}' if step_number > 14 else 'guide'),
            InlineKeyboardButton("Следующий шаг" if step_number < 36 else "Вернуться к методичке", callback_data=f'step{step_number + 1}' if step_number < 36 else 'part5')
        ],
        [InlineKeyboardButton("Вернуться к методичке", callback_data='guide')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Функция для отображения части 1 методички
async def show_part1(update: Update, context: ContextTypes):
    part_text = "Установка антидетект браузера AdsPower"
    keyboard = [
        [InlineKeyboardButton("Шаг 1", callback_data='step1'), InlineKeyboardButton("Шаг 2", callback_data='step2')],
        [InlineKeyboardButton("Шаг 3", callback_data='step3')],
        [InlineKeyboardButton("Вернуться к методичке", callback_data='guide')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(part_text, reply_markup=reply_markup)

# Функция для отображения шага 1
async def show_step1(update: Update, context: ContextTypes):
    step_text = (
        "Регистрируемся на сайте AdsPower по ссылке:\n"
        "[🔗 AdsPower](https://activity.adspower.com/ap/dist-ru/?utm_source=google&utm_medium=cpc&utm_term=%E4%B8%9A%E5%8A%A1%E5%9C%BA%E6%99%AF-RU-COM&utm_content=brand&utm_campaign=adspower&gad_source=1&gclid=Cj0KCQjw_-GxBhC1ARIsADGgDjsMhZ3IxQwwKRPsviBJyah1LXtUAN8xzVTjnBJgsuJFChZiXjdLj0waAtlMEALw_wcB)\n"
        "и скачиваем антидетект браузер."
    )
    photo_url = "https://prnt.sc/TJUMhBHujhOC"
    await update.callback_query.message.reply_photo(photo=photo_url, caption=step_text, parse_mode="Markdown")
    keyboard = [
        [InlineKeyboardButton("Вернуться к методичке", callback_data='guide'),
         InlineKeyboardButton("Следующий шаг", callback_data='step2')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Функция для отображения шага 2
async def show_step2(update: Update, context: ContextTypes):
    step_text = (
        "Авторизируемся в десктопной версии тем же логином и паролем, что вводили на сайте. "
        "Теперь у вас есть возможность добавить 10 бесплатных аккаунтов Facebook."
    )
    keyboard = [
        [InlineKeyboardButton("Предыдущий шаг", callback_data='step1'),
         InlineKeyboardButton("Следующий шаг", callback_data='part2')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(text=step_text, reply_markup=reply_markup)

# Функция для отображения шага 3
async def show_step3(update: Update, context: ContextTypes):
    step_text = "Дополнительный шаг 3."
    keyboard = [
        [InlineKeyboardButton("Предыдущий шаг", callback_data='step2'),
         InlineKeyboardButton("Следующий шаг", callback_data='part2')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(text=step_text, reply_markup=reply_markup)

# Функция для отображения части 2 методички
async def show_part2(update: Update, context: ContextTypes):
    messages = [
        ("2.1) На левой панели нажимаем на 'Прокси' и нажимаем 'Добавить прокси'", "https://prnt.sc/TPw1PpRds5iv"),
        ("2.2) Тут ничего не трогаем", "https://prnt.sc/87cY97lgmlJk"),
        ("2.3) В это поле вносим все данные прокси, согласно шаблону слева\nВАЖНО: в начале строки указать socks5://", "https://prnt.sc/4vqj0Pm-nxJc")
    ]
    for text, image_url in messages:
        await update.callback_query.message.reply_photo(photo=image_url, caption=text, parse_mode="Markdown")
    keyboard = [[InlineKeyboardButton("Вернуться к методичке", callback_data='guide')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Выберите:", reply_markup=reply_markup)

# Функция для отображения части 3 методички
async def show_part3(update: Update, context: ContextTypes):
    steps_buttons = [
        [InlineKeyboardButton("Шаг 1", callback_data='step4'), InlineKeyboardButton("Шаг 2", callback_data='step5')],
        [InlineKeyboardButton("Шаг 3", callback_data='step6'), InlineKeyboardButton("Шаг 4", callback_data='step7')],
        [InlineKeyboardButton("Шаг 5", callback_data='step8'), InlineKeyboardButton("Шаг 6", callback_data='step9')],
        [InlineKeyboardButton("Шаг 7", callback_data='step10'), InlineKeyboardButton("Шаг 8", callback_data='step11')],
        [InlineKeyboardButton("Вернуться к методичке", callback_data='guide')]
    ]
    reply_markup = InlineKeyboardMarkup(steps_buttons)
    await update.callback_query.message.edit_text(text="**Добавление аккаунта в AdsPower**\n\nВыберите шаг:", reply_markup=reply_markup)

# Функция для отображения шагов
async def show_step(update: Update, context: ContextTypes, step_data: str):
    steps = {
        'step4': ("Шаг 1", "Нажимаем кнопку 'Новый профиль'", "https://prnt.sc/RLZR6Jxrqr92"),
        'step5': ("Шаг 2", "В поле 'Имя' вводим название аккаунта, должно совпадать с названием папки в котором находится акк", "https://prnt.sc/-8543c_Q1WSh"),
        'step6': ("Шаг 3", "Выбираем группу, по дефолту у вас должна быть одна группа", "https://prnt.sc/vZ-MQaG7GthI"),
        'step7': ("Шаг 4", "Проверяем настройки, они должны совпадать со скрином, но если у вас ПК на Windows то не забываем это изменить", "https://prnt.sc/qgT8IsyC5NEk"),
        'step8': ("Шаг 5", "В папке с аккаунтом, у вас есть файл с куки, копируем текст из этого файла, и вставляем в поле на которое указывает стрелка", "https://prnt.sc/kxbI1SlLiZ9-"),
        'step9': ("Шаг 6", "Нажимаем на кнопку 'Сохраненные прокси' и ниже из выпадающего списка выбираем нашу прокси", "https://prnt.sc/iVoAbFCyePL7"),
        'step10': ("Шаг 7", "Нажимаем 'Новый отпечаток'", "https://prnt.sc/V6AuxDOvLQlc"),
        'step11': ("Шаг 8", "Нажимаем 'Ок' и ваш аккаунт заведен", "https://prnt.sc/-N9DNr7Y3oGr")
    }
    step_title, step_text, image_url = steps[step_data]
    await update.callback_query.message.reply_photo(photo=image_url, caption=f"{step_title}\n{step_text}", parse_mode="Markdown")
    step_number = int(step_data[-1])
    keyboard = [
        [
            InlineKeyboardButton("Предыдущий шаг" if step_number > 4 else "Вернуться к методичке", callback_data=f'step{step_number - 1}' if step_number > 4 else 'guide'),
            InlineKeyboardButton("Следующий шаг" if step_number < 11 else "Вернуться к методичке", callback_data=f'step{step_number + 1}' if step_number < 11 else 'part3')
        ],
        [InlineKeyboardButton("Вернуться к методичке", callback_data='guide')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Функция для отображения админ панели
async def show_admin_panel(update: Update, context: ContextTypes):
    admin_buttons = [
        [InlineKeyboardButton("Отправить сообщение всем пользователям", callback_data='broadcast')],
        [InlineKeyboardButton("Статистика пользователей", callback_data='user_stats')],
        [InlineKeyboardButton("Запросы от пользователей", callback_data='user_questions')],
        [InlineKeyboardButton("Вернуться в меню", callback_data='back_main')]
    ]
    reply_markup = InlineKeyboardMarkup(admin_buttons)
    await update.callback_query.message.edit_text(text="Выберите действие:", reply_markup=reply_markup)

# Функция для отображения статистики пользователей
async def show_user_stats(update: Update, context: ContextTypes):
    user_count = len(get_all_chat_ids())
    new_users_today = 0  # Замените на реальное значение
    new_users_week = 0  # Замените на реальное значение
    stats_text = (
        f"Общее количество пользователей: {user_count}\n"
        f"Новых пользователей за сегодня: {new_users_today}\n"
        f"Новых пользователей за неделю: {new_users_week}"
    )
    await update.callback_query.message.edit_text(text=stats_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад в админ панель", callback_data='admin_panel')]]))

# Функция для отображения запросов от пользователей
async def show_user_questions(update: Update, context: ContextTypes):
    questions = get_all_user_questions()
    if not questions:
        await update.callback_query.message.edit_text(text="Нет запросов от пользователей.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад в админ панель", callback_data='admin_panel')]]))
    else:
        for question in questions:
            question_id, chat_id, question_time, question_text = question
            message_text = (
                f"Chat ID пользователя: {chat_id}\n"
                f"Время отправки запроса: {question_time}\n"
                f"Текст сообщения: {question_text}"
            )
            keyboard = [
                [
                    InlineKeyboardButton("Ответить пользователю", callback_data=f'answer_{question_id}'),
                    InlineKeyboardButton("Назад в панель", callback_data='admin_panel')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.message.reply_text(message_text, reply_markup=reply_markup)

# Функция для обработки нажатия кнопки "Ответить пользователю"
async def handle_answer_button(update: Update, context: ContextTypes, button_data: str):
    question_id = button_data.split('_')[1]
    context.user_data['current_question_id'] = question_id
    await update.callback_query.message.reply_text("Введите ответ на вопрос пользователя:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data='admin_panel')]]))
    context.user_data['waiting_for_answer'] = True

# Запуск бота
def main() -> None:
    create_table()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_id", get_chat_id))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

# Функция запуска отслеживания файла
def watch_and_restart():
    file_to_watch = os.path.abspath(__file__)
    event_handler = RestartOnChange(file_to_watch)
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(file_to_watch), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    from threading import Thread
    watcher_thread = Thread(target=watch_and_restart, daemon=True)
    watcher_thread.start()
    main()
