import os
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str
    LOG_LEVEL: str = "INFO"


def get_config() -> Config:
    # token = os.getenv("BOT_TOKEN")
    token = "8563640047:AAEefEsTrT9PaR7ONYff82StoUkQwYOOKWI"
    if not token:
        raise SystemExit("Please set BOT_TOKEN environment variable")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    print(token)
    return Config(BOT_TOKEN=token, LOG_LEVEL=log_level)

get_config()