# bot.py
import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode

from config import get_config
from llm_handler import LLMHandler, ConversationManager

# Настройка логирования
cfg = get_config()
logging.basicConfig(
    level=getattr(logging, cfg.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramBot:
    """Основной класс бота"""
    
    def __init__(self, config):
        self.config = config
        self.bot = Bot(token=config.BOT_TOKEN)
        self.dp = Dispatcher()
        
        # Инициализация LLM
        llm_config = config.get_llm_config()
        self.llm_handler = LLMHandler(llm_config)
        self.conversation_manager = ConversationManager()
        
        # Данные бота
        self.bot_info = None
        self.bot_username = None
        
        # Регистрация обработчиков
        self.register_handlers()
    
    def register_handlers(self):
        """Регистрация всех обработчиков"""
        
        # Обработчик сообщений в группе
        @self.dp.message(F.chat.id == self.config.GROUP_ID)
        async def handle_group_message(message: types.Message):
            await self.process_group_message(message)
        
        # Команды для управления
        @self.dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            await self.cmd_start(message)
        
        @self.dp.message(Command("test"))
        async def cmd_test(message: types.Message):
            await self.cmd_test(message)
        
        @self.dp.message(Command("ping"))
        async def cmd_ping(message: types.Message):
            await self.cmd_ping(message)
        
        @self.dp.message(Command("models"))
        async def cmd_models(message: types.Message):
            await self.cmd_models(message)
        
        @self.dp.message(Command("clear"))
        async def cmd_clear(message: types.Message):
            await self.cmd_clear(message)
    
    async def initialize(self):
        """Инициализация бота"""
        await self.bot.delete_webhook(drop_pending_updates=True)
        
        # Получаем информацию о боте
        self.bot_info = await self.bot.get_me()
        self.bot_username = self.bot_info.username.lower()
        
        # Запускаем LLM handler
        await self.llm_handler.start()
        
        logger.info(f"🤖 Бот @{self.bot_username} инициализирован")
        logger.info(f"📢 Группа ID: {self.config.GROUP_ID}")
        logger.info(f"🧠 LLM модель: {self.config.OPENROUTER_MODEL}")
    
    async def process_group_message(self, message: types.Message):
        """Обработка сообщений в группе"""
        text = message.text or message.caption or ""
        
        if not text:
            return
        
        logger.info(f"📨 Сообщение от @{message.from_user.username}: {text[:100]}")
        
        # Проверяем упоминание бота
        pattern = rf"@{re.escape(self.bot_username)}(?:\s+|$)"
        
        if re.search(pattern, text, re.IGNORECASE):
            # Извлекаем запрос
            query = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
            
            if not query:
                await message.reply(
                    f"Привет! Я бот с поддержкой ИИ. Задайте вопрос после упоминания.\n"
                    f"Пример: @{self.bot_username} расскажи о Python"
                )
                return
            
            # Отправляем статус "печатает"
            await message.chat.do("typing")
            
            # Получаем контекст беседы
            context = self.conversation_manager.get_context(message.chat.id)
            
            try:
                # Генерируем ответ через LLM
                response = await self.llm_handler.generate_response(query, context)
                
                # Отправляем ответ
                await message.reply(
                    f"🤖 **Ответ:**\n{response}",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Сохраняем в историю
                self.conversation_manager.add_message(
                    message.chat.id, 
                    query, 
                    response
                )
                
                logger.info(f"✅ Ответ отправлен ({len(response)} символов)")
                
            except Exception as e:
                logger.error(f"❌ Ошибка LLM: {e}")
                await message.reply(
                    "Извините, произошла ошибка при обработке запроса. "
                    "Попробуйте позже или обратитесь к администратору."
                )
        
        # Обработка команд
        elif text.startswith("/"):
            if text.startswith("/help"):
                help_text = (
                    f"🆘 **Помощь по боту @{self.bot_username}**\n\n"
                    f"**Основное использование:**\n"
                    f"• Упоминание + вопрос: `@{self.bot_username} [ваш вопрос]`\n"
                    f"• Пример: `@{self.bot_username} расскажи о машинном обучении`\n\n"
                    f"**Команды:**\n"
                    f"• `/help` - эта справка\n"
                    f"• `/ping` - проверка работы\n"
                    f"• `/models` - список моделей\n"
                    f"• `/clear` - очистить историю диалога\n"
                    f"• `/test` - тестовая команда\n\n"
                    f"**Текущая модель:** `{self.config.OPENROUTER_MODEL}`"
                )
                await message.reply(help_text, parse_mode=ParseMode.MARKDOWN)
            
            elif text.startswith("/ping"):
                await message.reply("🏓 Понг! Бот и LLM работают корректно.")
    
    async def cmd_start(self, message: types.Message):
        """Команда /start"""
        await message.answer(
            f"🤖 **Бот с поддержкой ИИ**\n\n"
            f"• Username: @{self.bot_username}\n"
            f"• Модель: {self.config.OPENROUTER_MODEL}\n"
            f"• Группа: {self.config.GROUP_ID}\n\n"
            f"Используйте в группе: `@{self.bot_username} [вопрос]`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def cmd_test(self, message: types.Message):
        """Команда /test"""
        try:
            test_msg = await self.bot.send_message(
                self.config.GROUP_ID,
                f"🧪 **Тестовое сообщение**\n\n"
                f"Бот @{self.bot_username} работает!\n"
                f"Попробуйте: `@{self.bot_username} привет`",
                parse_mode=ParseMode.MARKDOWN
            )
            await message.answer(f"✅ Тест отправлен! ID: {test_msg.message_id}")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
    
    async def cmd_ping(self, message: types.Message):
        """Команда /ping"""
        await message.answer("✅ Бот активен! Проверьте LLM с помощью команды /test в группе.")
    
    async def cmd_models(self, message: types.Message):
        """Команда /models - показать доступные модели"""
        try:
            models = await self.llm_handler.get_models()
            if models:
                model_list = "\n".join([f"• {m.get('id', 'N/A')}" for m in models[:10]])
                await message.answer(
                    f"🧠 **Доступные модели (первые 10):**\n\n{model_list}\n\n"
                    f"Текущая: `{self.config.OPENROUTER_MODEL}`",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await message.answer("Не удалось получить список моделей.")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
    
    async def cmd_clear(self, message: types.Message):
        """Команда /clear - очистить историю"""
        if message.chat.id == self.config.GROUP_ID:
            self.conversation_manager.clear_history(message.chat.id)
            await message.reply("🗑️ История диалога очищена!")
        else:
            await message.answer("Эта команда работает только в группе.")
    
    async def run(self):
        """Запуск бота"""
        await self.initialize()
        
        logger.info("=" * 60)
        logger.info(f"🚀 БОТ ЗАПУЩЕН")
        logger.info(f"🤖 @{self.bot_username}")
        logger.info(f"📢 Группа: {self.config.GROUP_ID}")
        logger.info(f"🧠 Модель: {self.config.OPENROUTER_MODEL}")
        logger.info("=" * 60)
        
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Ошибка при работе бота: {e}")
        finally:
            await self.llm_handler.close()
            await self.bot.session.close()

async def main():
    """Основная функция"""
    config = get_config()
    bot = TelegramBot(config)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())