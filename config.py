import os
from dataclasses import dataclass

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Конфигурация приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # OpenRouter API
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    # OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "arcee-ai/trinity-large-preview:free")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "tngtech/deepseek-r1t-chimera:free")
    
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Group ID
    GROUP_ID: int = int(os.getenv("GROUP_ID", "-1003888548385"))
    
    # LLM Settings
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "500"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    def validate(self):
        """Проверка обязательных полей"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен")
        if not self.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY не установлен")
        
        return self
    
    def get_llm_config(self):
        """Получить конфигурацию для LLM"""
        from llm_handler import LLMConfig
        return LLMConfig(
            api_key=self.OPENROUTER_API_KEY,
            model=self.OPENROUTER_MODEL,
            max_tokens=self.LLM_MAX_TOKENS,
            temperature=self.LLM_TEMPERATURE
        )

def get_config() -> Config:
    """Получить конфигурацию"""
    return Config().validate()