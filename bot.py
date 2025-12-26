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

# ===================== CONFIG =====================

TOKEN = os.getenv("BOT_TOKEN")  # MUST be set in environment
ADMIN_CHANNEL_ID = -1003587825401
PUBLIC_CHANNEL_ID = -1003682833315

PROFILE_FILE = "profiles.json"
COUNTER_FILE = "counter.txt"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===================== PROFILE SYSTEM =====================

def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profiles(data):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_profile(user_id, username):
    profiles = load_profiles()
    uid = str(user_id)

    if uid not in profiles:
        profiles[uid] = {
            "name": username or "Anonymous",
            "aura": 0,
            "followers": 0,
            "following": 0,
            "bio": "No bio set"
        }
        save_profiles(profiles)

    return profiles[uid]

def increase_aura(user_id):
    profiles = load_profiles()
    uid = str(user_id)
    if uid in profiles:
        profiles[uid]["aura"] += 1
        save_profiles(profiles)

def calculate_score(profile):
    return (profile["aura"] * 3) + (profile["followers"] * 2)

# ===================== CONFESSION COUNTER =====================

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

# ===================== COMMANDS =====================

@dp.message(CommandStart())
async def start_handler(message: Message):
    get_profile(message.from_user.id, message.from_user.first_name)
    await message.answer(
        "Welcome 👋\n\n"
        "Send your confession anonymously.\n"
        "It will be reviewed before posting."
    )

@dp.message(F.text == "/profile")
async def profile_handler(message: Message):
    profile = get_profile(message.from_user.id, message.from_user.first_name)
    score = calculate_score(profile)

    await message.answer(
        f"{profile['name']}\n\n"
        f"⚡ Aura: {profile['aura']}\n"
        f"👥 Followers: {profile['followers']} | Following: {profile['following']}\n"
        f"⭐ Score: {score}\n\n"
        f"{profile['bio']}"
    )

@dp.message(F.text == "/rank")
async def rank_handler(message: Message):
    profiles = load_profiles()

    if not profiles:
        await message.answer("No users ranked yet.")
        return

    ranked = []
    for profile in profiles.values():
        ranked.append((profile["name"], profile["aura"], profile["followers"], calculate_score(profile)))

    ranked.sort(key=lambda x: x[3], reverse=True)

    text = "🏆 Top Contributors\n\n"
    for i, (name, aura, followers, score) in enumerate(ranked[:10], start=1):
        text += (
            f"{i}. {name}\n"
            f"   ⚡ Aura: {aura} | 👥 Followers: {followers}\n"
            f"   ⭐ Score: {score}\n\n"
        )

    await message.answer(text)

# ===================== CONFESSION FLOW =====================

@dp.message(F.text & ~F.text.startswith("/"))
async def confession_handler(message: Message):
    get_profile(message.from_user.id, message.from_user.first_name)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{message.from_user.id}:{message.message_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data="reject"),
            ]
        ]
    )

    await bot.send_message(
        ADMIN_CHANNEL_ID,
        f"📩 New Confession:\n\n{message.text}",
        reply_markup=keyboard
    )

    await message.answer("✅ Your confession was sent for review.")

# ===================== ADMIN ACTIONS =====================

@dp.callback_query(F.data.startswith("approve"))
async def approve_confession(callback: CallbackQuery):
    _, user_id, _ = callback.data.split(":")
    text = callback.message.text.replace("📩 New Confession:\n\n", "")

    confession_number = increase_counter()
    increase_aura(user_id)

    await bot.send_message(
        PUBLIC_CHANNEL_ID,
        f"📝 Anonymous Confession #{confession_number}\n\n{text}"
    )

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Approved as Confession #{confession_number}"
    )

    await callback.answer("Posted")

@dp.callback_query(F.data == "reject")
async def reject_confession(callback: CallbackQuery):
    await callback.message.edit_text(callback.message.text + "\n\n❌ Rejected")
    await callback.answer("Rejected")

# ===================== RUN =====================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
