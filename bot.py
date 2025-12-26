import asyncio
import os
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")  # set this in environment
ADMIN_CHANNEL_ID = -1003587825401     # admin review channel
PUBLIC_CHANNEL_ID = -1003682833315    # public confession channel

PROFILE_FILE = "profiles.json"
COUNTER_FILE = "counter.txt"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= UTILITIES =================
def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profiles(data):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_profile(user_id, name):
    profiles = load_profiles()
    uid = str(user_id)

    if uid not in profiles:
        profiles[uid] = {
            "name": name or "Anonymous",
            "aura": 0,
            "followers": 0,
            "following": 0,
            "bio": "No bio set"
        }
        save_profiles(profiles)

    return profiles[uid]

def get_counter():
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, "r") as f:
        return int(f.read().strip())

def increase_counter():
    count = get_counter() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

# ================= UI =================
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧑 My Profile")],
            [KeyboardButton(text="✍️ Send Confession")]
        ],
        resize_keyboard=True
    )

# ================= HANDLERS =================
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Welcome 👋\n\n"
        "This is an anonymous confession bot.\n"
        "Choose an option below 👇",
        reply_markup=main_menu()
    )

@dp.message(F.text == "🧑 My Profile")
async def profile_handler(message: Message):
    profile = get_profile(message.from_user.id, message.from_user.first_name)

    await message.answer(
        f"{profile['name']}\n\n"
        f"⚡︎ Aura: {profile['aura']}\n"
        f"👥 Followers: {profile['followers']} | Following: {profile['following']}\n\n"
        f"{profile['bio']}",
        reply_markup=main_menu()
    )

@dp.message(F.text == "✍️ Send Confession")
async def send_confession_hint(message: Message):
    await message.answer(
        "✍️ Send your confession now.\n"
        "It will be reviewed before posting.",
        reply_markup=main_menu()
    )

@dp.message(
    F.text
    & ~F.text.startswith("🧑")
    & ~F.text.startswith("✍️")
)
async def confession_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data="reject"),
            ]
        ]
    )

    await bot.send_message(
        ADMIN_CHANNEL_ID,
        f"📩 New Confession\n\n{message.text}",
        reply_markup=keyboard
    )

    await message.answer(
        "✅ Your confession was sent for review.",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data.startswith("approve"))
async def approve_confession(callback: CallbackQuery):
    user_id = callback.data.split(":")[1]
    text = callback.message.text.replace("📩 New Confession\n\n", "")
    confession_number = increase_counter()

    await bot.send_message(
        PUBLIC_CHANNEL_ID,
        f"📝 Anonymous Confession #{confession_number}\n\n{text}"
    )

    profiles = load_profiles()
    if user_id in profiles:
        profiles[user_id]["aura"] += 1
        save_profiles(profiles)

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Approved as Confession #{confession_number}"
    )
    await callback.answer("Posted")

@dp.callback_query(F.data == "reject")
async def reject_confession(callback: CallbackQuery):
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ Rejected"
    )
    await callback.answer("Rejected")

# ================= START =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
