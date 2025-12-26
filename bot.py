import asyncio
import os
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    BotCommand
)

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID"))
PUBLIC_CHANNEL_ID = int(os.getenv("PUBLIC_CHANNEL_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= FILES =================
PROFILE_FILE = "profiles.json"
COUNTER_FILE = "counter.txt"

CONFESS_MODE = set()
SETNAME_MODE = set()
SETBIO_MODE = set()

# ================= UTILS =================
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
            "bio": "No bio set",
            "aura": 0,
            "followers": 0,
            "following": 0
        }
        save_profiles(profiles)

    return profiles[uid]

def update_profile(user_id, key, value):
    profiles = load_profiles()
    profiles[str(user_id)][key] = value
    save_profiles(profiles)

def increase_counter():
    count = 1
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            count = int(f.read()) + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    return count

# ================= START =================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Welcome to XConfession Bot\n\n"
        "Send confessions anonymously.\n"
        "Admins review before posting.\n\n"
        "Use the menu ⬇️"
    )

# ================= PROFILE =================
@dp.message(Command("profile"))
async def profile(message: Message):
    p = get_profile(message.from_user.id)
    await message.answer(
        f"{p['name']}\n\n"
        f"⚡ Aura: {p['aura']}\n"
        f"👥 Followers: {p['followers']} | Following: {p['following']}\n\n"
        f"{p['bio']}"
    )

# ================= SET NAME =================
@dp.message(Command("setname"))
async def setname(message: Message):
    SETNAME_MODE.add(message.from_user.id)
    await message.answer("✍️ Send your new name")

# ================= SET BIO =================
@dp.message(Command("setbio"))
async def setbio(message: Message):
    SETBIO_MODE.add(message.from_user.id)
    await message.answer("📝 Send your bio")

# ================= CONFESS =================
@dp.message(Command("confess"))
async def confess(message: Message):
    CONFESS_MODE.add(message.from_user.id)
    await message.answer("📝 Send your confession")

# ================= CANCEL =================
@dp.message(Command("cancel"))
async def cancel(message: Message):
    CONFESS_MODE.discard(message.from_user.id)
    SETNAME_MODE.discard(message.from_user.id)
    SETBIO_MODE.discard(message.from_user.id)
    await message.answer("❌ Action cancelled")

# ================= TEXT HANDLER =================
@dp.message(F.text)
async def text_handler(message: Message):
    uid = message.from_user.id

    if uid in SETNAME_MODE:
        update_profile(uid, "name", message.text[:20])
        SETNAME_MODE.remove(uid)
        await message.answer("✅ Name updated")
        return

    if uid in SETBIO_MODE:
        update_profile(uid, "bio", message.text[:80])
        SETBIO_MODE.remove(uid)
        await message.answer("✅ Bio updated")
        return

    if uid in CONFESS_MODE:
        CONFESS_MODE.remove(uid)

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

        await message.answer("✅ Confession sent for review")
        return

    await message.answer("❗ Use the menu to interact")

# ================= ADMIN =================
@dp.callback_query(F.data == "approve")
async def approve(callback: CallbackQuery):
    text = callback.message.text.replace("📩 New Confession:\n\n", "")
    number = increase_counter()

    await bot.send_message(
        PUBLIC_CHANNEL_ID,
        f"📝 Anonymous Confession #{number}\n\n{text}"
    )

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Approved #{number}"
    )
    await callback.answer("Posted")

@dp.callback_query(F.data == "reject")
async def reject(callback: CallbackQuery):
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ Rejected"
    )
    await callback.answer("Rejected")

# ================= COMMAND MENU =================
async def setup_commands():
    commands = [
        BotCommand(command="start", description="Start bot"),
        BotCommand(command="confess", description="Submit confession"),
        BotCommand(command="profile", description="View profile"),
        BotCommand(command="setname", description="Set name"),
        BotCommand(command="setbio", description="Set bio"),
        BotCommand(command="cancel", description="Cancel action"),
    ]
    await bot.set_my_commands(commands)

# ================= RUN =================
async def main():
    await setup_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
