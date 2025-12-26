import asyncio
import os
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID"))
PUBLIC_CHANNEL_ID = int(os.getenv("PUBLIC_CHANNEL_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

PROFILE_FILE = "profiles.json"
COUNTER_FILE = "counter.txt"

def load_json(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_profile(user):
    profiles = load_json(PROFILE_FILE, {})
    uid = str(user.id)

    if uid not in profiles:
        profiles[uid] = {
            "name": user.first_name or "Anonymous",
            "aura": 0,
            "followers": 0,
            "following": 0,
            "bio": "No bio set"
        }
        save_json(PROFILE_FILE, profiles)

    return profiles[uid]

def increase_counter():
    count = int(open(COUNTER_FILE).read()) if os.path.exists(COUNTER_FILE) else 0
    count += 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

@dp.message(CommandStart())
async def start(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧑 My Profile", callback_data="profile")]
        ]
    )
    await message.answer(
        "Welcome 👋\n\nSend your confession anonymously.",
        reply_markup=kb
    )

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    p = get_profile(callback.from_user)
    await callback.message.answer(
        f"{p['name']}\n\n"
        f"⚡ Aura: {p['aura']}\n"
        f"👥 Followers: {p['followers']} | Following: {p['following']}\n\n"
        f"{p['bio']}"
    )
    await callback.answer()

@dp.message(F.text)
async def confession(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{message.from_user.id}:{message.text}"),
                InlineKeyboardButton(text="❌ Reject", callback_data="reject")
            ]
        ]
    )

    await bot.send_message(
        ADMIN_CHANNEL_ID,
        f"📩 New Confession:\n\n{message.text}",
        reply_markup=kb
    )

    await message.answer("✅ Your confession was sent for review.")

@dp.callback_query(F.data.startswith("approve"))
async def approve(callback: CallbackQuery):
    _, user_id, text = callback.data.split(":", 2)
    confession_number = increase_counter()

    await bot.send_message(
        PUBLIC_CHANNEL_ID,
        f"📝 Confession #{confession_number}\n\n{text}"
    )

    profiles = load_json(PROFILE_FILE, {})
    if user_id in profiles:
        profiles[user_id]["aura"] += 1
        save_json(PROFILE_FILE, profiles)

    await callback.message.edit_text("✅ Approved & Posted")
    await callback.answer()

@dp.callback_query(F.data == "reject")
async def reject(callback: CallbackQuery):
    await callback.message.edit_text("❌ Rejected")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
