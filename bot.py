import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import get_config


cfg = get_config()
logging.basicConfig(level=getattr(logging, cfg.LOG_LEVEL.upper(), logging.INFO))


async def main():
	bot = Bot(token=cfg.BOT_TOKEN)
	dp = Dispatcher()
    
	await bot.delete_webhook(drop_pending_updates=True)
	print("Webhook deleted successfully!")

	@dp.message(Command("start"))
	async def cmd_start(message: types.Message):
	    await message.answer("Привет! Я бот на aiogram 3.x!")
    
	@dp.message()
	async def echo(message: types.Message):
	    await message.answer(f"Вы сказали: {message.text}")
    
	await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

