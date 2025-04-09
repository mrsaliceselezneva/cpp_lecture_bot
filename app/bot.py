import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from app.config import BOT_TOKEN, ADMINS
from app.db import (
    add_user, get_users, add_video, get_videos, get_all_users,
    remove_user, remove_video_by_link, search_videos_by_title
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Команда /start
    if text.startswith("/start"):
        if user_id in get_users():
            await message.answer("👋 Добро пожаловать! У вас есть доступ к видео.")
        elif user_id in ADMINS:
            add_user(user_id, message.from_user.first_name, message.from_user.last_name or "")
            await message.answer("👋 Вы были автоматически добавлены как администратор.")
        else:
            await message.answer("🚫 У вас нет доступа к боту. Обратитесь к администратору.")
        return

    if text.startswith("/users") and user_id in ADMINS:
        users = get_all_users()
        if users:
            msg = "👥 Пользователи:\n" + "\n".join([str(u[0]) for u in users])
            await message.answer(msg)
        else:
            await message.answer("📭 Пока нет пользователей.")
        return

    # Команда /videos — показать все ссылки
    if text.startswith("/videos"):
        if user_id not in get_users():
            await message.answer("🚫 У вас нет доступа.")
            return

        videos = get_videos()
        if videos:
            msg = "\n\n".join([f"*{v['title']}*\n{v['link']}" for v in videos])
            await message.answer(msg, parse_mode="Markdown")
        else:
            await message.answer("📭 Пока нет видео.")
        return

    if text.startswith("/add_user") and user_id in ADMINS:
        lines = text.strip().split("\n")[1:]  # пропускаем первую строку с "/add_user"
        if not lines:
            await message.answer("❗ Пример:\n/add_user\n123456789 Иван Иванов\n987654321 Пётр Петров")
            return

        added = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3:
                try:
                    uid = int(parts[0])
                    first_name = parts[1]
                    last_name = " ".join(parts[2:])
                    add_user(uid, first_name, last_name)
                    added.append(f"{first_name} {last_name} ({uid})")
                except ValueError:
                    continue

        if added:
            msg = "✅ Добавлены пользователи:\n" + "\n".join(added)
            await message.answer(msg)
        else:
            await message.answer(
                "❗ Ни одного корректного пользователя не найдено. Пример:\n/add_user\n123456789 Иван Иванов")
        return

    # Команда /add — добавить ссылку (только для админа)
    if text.startswith("/add_video") and user_id in ADMINS:
        lines = text.strip().split("\n")[1:]  # пропускаем первую строку с "/add"
        if not lines:
            await message.answer("❗ Пример:\n/add_video\nЛекция 1 | https://...\nЛекция 2 | https://...")
            return

        added = []
        for line in lines:
            if "|" in line:
                title, link = map(str.strip, line.split("|", 1))
                add_video(title, link)
                added.append((title, link))

        if added:
            msg = "\n\n".join([f"*{title}*\n{link}" for title, link in added])
            for uid in get_users():
                try:
                    await bot.send_message(uid, f"📢 Добавлены новые видео:\n\n{msg}", parse_mode="Markdown")
                except Exception:
                    pass
            await message.answer("✅ Добавлено и разослано:")
        else:
            await message.answer("❗ Ни одной валидной строки не найдено. Пример:\n/add_video\nЛекция 1 | https://...")
        return

    # Удалить пользователя
    if text.startswith("/del_user") and user_id in ADMINS:
        parts = text.split()
        if len(parts) == 2:
            try:
                uid = int(parts[1])
                remove_user(uid)
                await message.answer(f"✅ Пользователь {uid} удалён.")
            except ValueError:
                await message.answer("❗ Неверный ID.")
        else:
            await message.answer("Пример: /del_user 123456789")
        return

    # Удалить видео по ID или ссылке
    if text.startswith("/del_video") and user_id in ADMINS:
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            arg = parts[1]
            remove_video_by_link(arg)
            await message.answer("✅ Видео по ссылке удалено.")
        else:
            await message.answer("Пример: /del_video https://...")
        return

    if text.startswith("/find"):
        keyword = text.replace("/find", "").strip()
        if not keyword:
            await message.answer("❗ Напиши слово для поиска. Пример: /find лекция")
            return

        results = search_videos_by_title(keyword)
        if results:
            msg = "\n\n".join([f"*{v['title']}*\n{v['link']}" for v in results])
            await message.answer(f"🔍 Найдено:\n\n{msg}", parse_mode="Markdown")
        else:
            await message.answer("🙁 Ничего не найдено.")
        return

    if text.startswith("/help"):
        if user_id in ADMINS:
            await message.answer(
                "🤖 Команды для администратора:\n"
                "/start – зарегистрироваться как админ\n"
                "/add_user ID Имя Фамилия – добавить пользователя\n"
                "/del_user ID – удалить пользователя\n"
                "/users – список пользователей\n"
                "/add Название | ссылка – добавить видео\n"
                "/del_video ссылка – удалить видео\n"
                "/videos – список видео\n"
                "/find ключевое слово – поиск по названию\n"
            )
        elif user_id in get_users():
            await message.answer(
                "🤖 Доступные команды:\n"
                "/start – войти в систему\n"
                "/videos – список доступных видео\n"
                "/find ключевое слово – поиск по названию\n"
            )
        else:
            await message.answer("🚫 У вас нет доступа к боту.")
        return


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
