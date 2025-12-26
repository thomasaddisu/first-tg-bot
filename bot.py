import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

TOKEN = os.getenv("BOT_TOKEN")  # set in environment
ADMIN_CHANNEL_ID = -1003587825401
PUBLIC_CHANNEL_ID = -1003682833315

bot = Bot(token=TOKEN)
dp = Dispatcher()

# /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Welcome 👋\n\n"
        "Send your confession anonymously.\n"
        "It will be reviewed before posting."
    )

# Receive confession
@dp.message(F.text)
async def confession_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Approve",
                    callback_data=f"approve:{message.message_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Reject",
                    callback_data=f"reject:{message.message_id}"
                ),
            ]
        ]
    )

    await bot.send_message(
        ADMIN_CHANNEL_ID,
        f"📩 New Confession:\n\n{message.text}",
        reply_markup=keyboard
    )

    await message.answer(
        "✅ Your confession was sent for review."
    )

# Handle approval
@dp.callback_query(F.data.startswith("approve"))
async def approve_confession(callback: CallbackQuery):
    text = callback.message.text.replace("📩 New Confession:\n\n", "")

    await bot.send_message(
        PUBLIC_CHANNEL_ID,
        f"📝 Anonymous Confession:\n\n{text}"
    )

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Approved and posted"
    )

    await callback.answer("Posted to public channel")

# Handle rejection
@dp.callback_query(F.data.startswith("reject"))
async def reject_confession(callback: CallbackQuery):
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ Rejected"
    )
    await callback.answer("Confession rejected")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
