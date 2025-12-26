import asyncio
import os
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# =========================
# ENV (Railway Safe)
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID"))
PUBLIC_CHANNEL_ID = int(os.getenv("PUBLIC_CHANNEL_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# FILES
# =========================
PROFILE_FILE = "profiles.json"
COUNTER_FILE = "counter.txt"

CONFESS_MODE = set()
SETNAME_MODE = set()

# =========================
# UTILS
# =========================
def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)

def save_profiles(data):
    with open(PROFILE_FILE, "w") as f:
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

def confession_count():
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, "r") as f:
        return int(f.read())

def increase_counter():
    count = confession_count() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

# =========================
# START
# =========================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Welcome to XConfession Bot\n\n"
        "Send confessions anonymously.\n"
        "All confessions are reviewed before posting.\n\n"
        "Use /help to see commands."
    )

# =========================
# HELP
# =========================
@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "/confess – Submit confession\n"
        "/profile – View profile\n"
        "/setname – Set custom name\n"
        "/rules – View rules\n"
        "/privacy – Privacy info\n"
        "/cancel – Cancel action"
    )

# =========================
# RULES
# =========================
@dp.message(Command("rules"))
async def rules(message: Message):
    await message.answer(
        "📜 Rules\n\n"
        "• No names\n"
        "• No hate\n"
        "• Be respectful"
    )

# =========================
# PRIVACY
# =========================
@dp.message(Command("privacy"))
async def privacy(message: Message):
    await message.answer(
        "🔐 Privacy\n\n"
        "• Confessions are anonymous\n"
        "• No personal data is shared\n"
        "• Admins cannot see sender"
    )

# =========================
# PROFILE
# =========================
@dp.message(Command("profile"))
async def profile(message: Message):
    p = get_profile(message.from_user.id)

    await message.answer(
        f"{p['name']}\n\n"
        f"⚡ Aura: {p['aura']}\n"
        f"👥 Followers: {p['followers']} | Following: {p['following']}\n\n"
        f"{p['bio']}"
    )

# =========================
# SET NAME
# =========================
@dp.message(Command("setname"))
async def setname(message: Message):
    SETNAME_MODE.add(message.from_user.id)
    await message.answer("✍️ Send the name you want to use.")

@dp.message(F.from_user.id.in_(lambda: SETNAME_MODE))
async def receive_name(message: Message):
    name = message.text.strip()[:20]
    update_profile(message.from_user.id, "name", name)
    SETNAME_MODE.remove(message.from_user.id)
    await message.answer(f"✅ Name set to: {name}")

# =========================
# CONFESS
# =========================
@dp.message(Command("confess"))
async def confess(message: Message):
    CONFESS_MODE.add(message.from_user.id)
    await message.answer("📝 Send your confession now.")

@dp.message(F.from_user.id.in_(lambda: CONFESS_MODE))
async def receive_confession(message: Message):
    CONFESS_MODE.remove(message.from_user.id)

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
# CANCEL
# =========================
@dp.message(Command("cancel"))
async def cancel(message: Message):
    CONFESS_MODE.discard(message.from_user.id)
    SETNAME_MODE.discard(message.from_user.id)
    await message.answer("❌ Action cancelled.")

# =========================
# ADMIN ACTIONS
# =========================
@dp.callback_query(F.data == "approve")
async def approve(callback: CallbackQuery):
    text = callback.message.text.replace("📩 New Confession:\n\n", "")
    number = increase_counter()

    await bot.send_message(
        PUBLIC_CHANNEL_ID,
        f"📝 Anonymous Confession #{number}\n\n{text}"
    )

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Approved as #{number}"
    )
    await callback.answer("Posted")

@dp.callback_query(F.data == "reject")
async def reject(callback: CallbackQuery):
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ Rejected"
    )
    await callback.answer("Rejected")

# =========================
# RUN
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
