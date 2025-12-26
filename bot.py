import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8234011884

bot = Bot(token=TOKEN)
dp = Dispatcher()

# /start command
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Welcome 👋\n\n"
        "This is an anonymous confession bot.\n"
        "Send your confession as a message.\n\n"
        "Rules:\n"
        "- No names\n"
        "- No hate\n"
        "- Be respectful"
    )

# Handle confessions
@dp.message()
async def confession_handler(message: Message):
    # Forward confession to admin
    await bot.send_message(
        ADMIN_ID,
        f"📩 New Confession:\n{message.text}"
    )

    # Reply to user
    await message.answer(
        "✅ Your confession was received anonymously.\n"
        "It will be reviewed before posting."
    )

# Run bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
