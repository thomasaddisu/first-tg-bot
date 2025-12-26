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

# =========================
# ENV VARIABLES (Railway)
# =========================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID"))
PUBLIC_CHANNEL_ID = int(os.getenv("PUBLIC_CHANNEL_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# FILES
# =========================
PROFILE_FILE = "profiles.json"
COUNTER_FILE = "counter.txt"

SET_NAME_MODE = set()

# =========================
# UTILS
# =========================
def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profiles(data):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_profile(user_id):
    profiles = load_profiles()
    uid = str(user_id)

    if uid not in profiles:
        profiles[uid] = {
            "name": "Not set",
            "aura": 0,
            "followers": 0,
            "following": 0,
            "bio": "No bio set"
        }
        save_profiles(profiles)

    return profiles[uid]

def update_profile(user_id, key, value):
    profiles = load_profiles()
    profiles[str(user_id)][key] = value
    save_profiles(profiles)

def get_counter():
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, "r") as f:
        return int(f.read())

def increase_counter():
    count = get_counter() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

# =========================
# START
# =========================
@dp.message(CommandStart())
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧑 My Profile", callback_data="profile")]
        ]
    )

    await message.answer(
        "👋 Welcome to XConfession Bot\n\n"
        "Send your confession anonymously.\n"
        "Admins will review before posting.\n\n"
        "Use /setname to choose your name.",
        reply_markup=keyboard
    )

# =========================
# PROFILE VIEW
# =========================
@dp.callback_query(F.data == "profile")
async def profile_view(callback: CallbackQuery):
    profile = get_profile(callback.from_user.id)

    await callback.message.answer(
        f"{profile['name']}\n\n"
        f"⚡ Aura: {profile['aura']}\n"
        f"👥 Followers: {profile['followers']} | Following: {profile['following']}\n\n"
        f"{profile['bio']}"
    )

    await callback.answer()

# =========================
# SET NAME FLOW (FIXED)
# =========================
@dp.message(F.text == "/setname")
async def setname_start(message: Message):
    SET_NAME_MODE.add(message.from_user.id)
    await message.answer("✍️ Send the name you want to use (max 20 characters).")

@dp.message(F.from_user.id.in_(lambda: SET_NAME_MODE))
async def receive_name(message: Message):
    name = message.text.strip()[:20]

    update_profile(message.from_user.id, "name", name)
    SET_NAME_MODE.remove(message.from_user.id)

    await message.answer(f"✅ Your name has been set to: {name}")

# =========================
# CONFESSION HANDLER
# =========================
@dp.message(F.text & ~F.text.startswith("/") & ~F.from_user.id.in_(lambda: SET_NAME_MODE))
async def confession_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data="approve"),
                InlineKeyboardButton(text="❌ Reject", callback_data="reject")
            ]
        ]
    )

    await bot.send_message(
        ADMIN_CHANNEL_ID,
        f"📩 New Confession:\n\n{message.text}",
        reply_markup=keyboard
    )

    await message.answer("✅ Confession sent for review.")

# =========================
# APPROVE CONFESSION
# =========================
@dp.callback_query(F.data == "approve")
async def approve_confession(callback: CallbackQuery):
    text = callback.message.text.replace("📩 New Confession:\n\n", "")
    confession_number = increase_counter()

    await bot.send_message(
        PUBLIC_CHANNEL_ID,
        f"📝 Anonymous Confession #{confession_number}\n\n{text}"
    )

    # Aura reward
    profile = get_profile(ADMIN_ID)
    profile["aura"] += 1
    update_profile(ADMIN_ID, "aura", profile["aura"])

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Approved as Confession #{confession_number}"
    )

    await callback.answer("Posted to public channel")

# =========================
# REJECT CONFESSION
# =========================
@dp.callback_query(F.data == "reject")
async def reject_confession(callback: CallbackQuery):
    await callback.message.edit_text(callback.message.text + "\n\n❌ Rejected")
    await callback.answer("Confession rejected")

# =========================
# RUN
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
