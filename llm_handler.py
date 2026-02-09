# llm_handler.py
import aiohttp
import json
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Конфигурация для LLM"""
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = ""
    max_tokens: int = 3000
    temperature: float = 0.7

class LLMHandler:
    """Обработчик запросов к LLM через OpenRouter"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def start(self):
        """Инициализация сессии"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/your-repo",  # Замените на ваш репозиторий
                    "X-Title": "Telegram Bot"  # Название вашего приложения
                }
            )
        logger.info("LLM handler started")
    
    async def close(self):
        """Закрытие сессии"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("LLM handler closed")
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        """
        Генерация ответа с помощью LLM
        
        Args:
            prompt: Запрос пользователя
            context: Контекст беседы (если есть)
            
        Returns:
            Сгенерированный ответ или сообщение об ошибке
        """
        if not self.session or self.session.closed:
            await self.start()
        
        # Формируем системный промпт
        system_message = {
            "role": "system",
            "content": "Ты полезный и дружелюбный помощник в Telegram-группе. "
                       "Отвечай кратко, понятно и по делу. "
                       "Будь вежливым и помогай пользователям. "
                       "Если не знаешь ответа, честно скажи об этом."
        }
        
        # Формируем сообщения для LLM
        messages = [system_message]
        
        # Добавляем контекст, если есть
        if context:
            messages.append({
                "role": "user",
                "content": context
            })
        
        # Добавляем текущий запрос
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": False
        }
        
        try:
            logger.debug(f"Sending request to LLM with prompt: {prompt}")
            
            async with self.session.post(
                f"{self.config.base_url}/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        reply = result["choices"][0]["message"]["content"].strip()
                        logger.debug(f"LLM response: {reply}")
                        return reply
                    else:
                        logger.error(f"Unexpected response format: {result}")
                        return "Извините, произошла ошибка при обработке запроса."
                
                elif response.status == 429:
                    logger.warning("Rate limit exceeded")
                    return "Извините, слишком много запросов. Попробуйте позже."
                
                elif response.status == 401:
                    logger.error("Invalid API key")
                    return "Извините, проблема с настройками бота. Обратитесь к администратору."
                
                else:
                    error_text = await response.text()
                    logger.error(f"LLM API error {response.status}: {error_text}")
                    return f"Извините, временные технические проблемы. (Код ошибки: {response.status})"
                    
        except asyncio.TimeoutError:
            logger.error("LLM request timeout")
            return "Извините, время ожидания ответа истекло. Попробуйте позже."
            
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return "Извините, произошла сетевая ошибка. Попробуйте позже."
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return "Извините, произошла непредвиденная ошибка."
    
    async def get_models(self) -> list:
        """Получить список доступных моделей"""
        if not self.session or self.session.closed:
            await self.start()
        
        try:
            async with self.session.get(f"{self.config.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                return []
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return []

class ConversationManager:
    """Менеджер контекста беседы"""
    
    def __init__(self, max_history: int = 10):
        self.conversations = {}  # {chat_id: [(user_msg, bot_msg), ...]}
        self.max_history = max_history
    
    def add_message(self, chat_id: int, user_message: str, bot_response: str):
        """Добавить сообщение в историю"""
        if chat_id not in self.conversations:
            self.conversations[chat_id] = []
        
        self.conversations[chat_id].append((user_message, bot_response))
        
        # Ограничиваем размер истории
        if len(self.conversations[chat_id]) > self.max_history:
            self.conversations[chat_id] = self.conversations[chat_id][-self.max_history:]
    
    def get_context(self, chat_id: int) -> str:
        """Получить контекст беседы для указанного чата"""
        if chat_id not in self.conversations or not self.conversations[chat_id]:
            return ""
        
        context_lines = []
        for user_msg, bot_msg in self.conversations[chat_id][-5:]:  # Берем последние 5 пар
            context_lines.append(f"Пользователь: {user_msg}")
            context_lines.append(f"Ассистент: {bot_msg}")
        
        return "\n".join(context_lines)
    
    def clear_history(self, chat_id: int):
        """Очистить историю для указанного чата"""
        if chat_id in self.conversations:
            del self.conversations[chat_id]