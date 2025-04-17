import os
import sqlite3
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio

# Подключение к базе данных SQLite
def get_db_connection():
    return sqlite3.connect('chat_ids.db')

# Создание таблицы для хранения chat IDs
def create_table():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_ids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL UNIQUE
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            question_time TEXT NOT NULL,
            question_text TEXT NOT NULL
        )
        ''')
        conn.commit()

# Функция для сохранения chat ID
def save_chat_id(chat_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO chat_ids (chat_id) VALUES (?)', (chat_id,))
        conn.commit()

# Функция для получения всех chat IDs
def get_all_chat_ids():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id FROM chat_ids')
        return [row[0] for row in cursor.fetchall()]

# Функция для сохранения вопроса пользователя
def save_user_question(chat_id, question_text):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_questions (chat_id, question_time, question_text) VALUES (?, ?, ?)',
                       (chat_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), question_text))
        conn.commit()

# Функция для получения всех вопросов пользователей
def get_all_user_questions():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, chat_id, question_time, question_text FROM user_questions')
        return cursor.fetchall()

# Функция для получения количества доступных аккаунтов из Google Sheets
def get_available_accounts_from_sheet(creds_file):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open("FB Accounts").sheet1
    data = sheet.get_all_records()
    available_accounts = {
        'king_farm': 0,
        'farm': 0,
        'autoreg': 0
    }
    for row in data:
        account_type = row.get('Type')
        status = row.get('Status')
        if account_type == 'king_farm' and status == 'available':
            available_accounts['king_farm'] += 1
        elif account_type == 'farm' and status == 'available':
            available_accounts['farm'] += 1
        elif account_type == 'autoreg' and status == 'available':
            available_accounts['autoreg'] += 1
    return available_accounts

# Функция для обработки запроса на получение аккаунтов
async def process_account_request(update, context, creds_file, product_id, quantity):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open("FB Accounts").sheet1
    data = sheet.get_all_records()
    available_accounts = [row for row in data if row['Type'] == product_id and row['Status'] == 'available']
    if len(available_accounts) < quantity:
        await update.callback_query.message.reply_text("Недостаточно аккаунтов в наличии.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='fb_king_farm')]]))
        return
    selected_accounts = available_accounts[:quantity]
    for account in selected_accounts:
        row_number = data.index(account) + 2
        sheet.update_cell(row_number, data[0].index('Status') + 1, 'DONE')
    file_path = f"/tmp/accounts_{product_id}_{update.effective_chat.id}.txt"
    with open(file_path, 'w') as file:
        for account in selected_accounts:
            file.write(f"{account['Account']}\n")
    await update.callback_query.message.reply_document(document=open(file_path, 'rb'), filename=f"accounts_{product_id}.txt", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='fb_king_farm')]]))
    os.remove(file_path)

# Класс для отслеживания изменений файла
class RestartOnChange(FileSystemEventHandler):
    def __init__(self, file_to_watch):
        self.file_to_watch = file_to_watch

    def on_modified(self, event):
        if event.src_path.endswith(self.file_to_watch):
            print(f"Файл {event.src_path} изменён. Перезапуск...")
            os.execv(sys.executable, ['python'] + sys.argv)
