# Обновлённый db.py с поддержкой имени и фамилии пользователей
import os
import sqlite3
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = "/db.sqlite3"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Обновлённая таблица пользователей с именем и фамилией
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    link TEXT
)
''')

conn.commit()


def add_user(user_id: int, first_name: str = "", last_name: str = ""):
    cursor.execute("INSERT OR IGNORE INTO users (id, first_name, last_name) VALUES (?, ?, ?)",
                   (user_id, first_name, last_name))
    conn.commit()


def get_users():
    return [row[0] for row in cursor.execute("SELECT id FROM users")]


def get_all_users():
    return cursor.execute("SELECT id, first_name, last_name FROM users").fetchall()


def remove_user(user_id: int):
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()


def add_video(title: str, link: str):
    match = re.match(r"(\d+)\.\s*(.+)", title)
    if match:
        # Есть номер в заголовке — использовать его
        theme_number = int(match.group(1))
        title_text = match.group(2)

        # Сдвигаем темы с номером >= theme_number
        cursor.execute("""
            UPDATE videos
            SET theme_number = theme_number + 1
            WHERE theme_number >= ?
            ORDER BY theme_number DESC
        """, (theme_number,))
    else:
        # Номера нет — определить следующий по порядку
        result = cursor.execute("SELECT MAX(theme_number) FROM videos").fetchone()
        theme_number = (result[0] or 0) + 1
        title_text = title.strip()

    # Добавить новое видео
    cursor.execute("""
        INSERT INTO videos (theme_number, title, link)
        VALUES (?, ?, ?)
    """, (theme_number, title_text, link))

    conn.commit()


def get_videos():
    return [
        {"title": f"Тема {row[0]}. {row[1]}", "link": row[2]}
        for row in cursor.execute("SELECT theme_number, title, link FROM videos ORDER BY theme_number")
    ]


def remove_video_by_link(link: str):
    cursor.execute("DELETE FROM videos WHERE link = ?", (link,))
    conn.commit()


def remove_video_by_number(theme_number: int):
    # Удаляем видео с указанным номером темы
    cursor.execute("DELETE FROM videos WHERE theme_number = ?", (theme_number,))

    # Сдвигаем остальные вниз
    cursor.execute("""
        UPDATE videos
        SET theme_number = theme_number - 1
        WHERE theme_number > ?
    """, (theme_number,))

    conn.commit()


def search_videos_by_title(keyword: str):
    return [
        {"title": row[0], "link": row[1]}
        for row in cursor.execute("SELECT title, link FROM videos WHERE title LIKE ?", (f"%{keyword}%",))
    ]
