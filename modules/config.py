import os


class Configuration:
    # telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    # webhook
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "").strip()
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8080"))
    # polling
    POLL_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "300"))
    # database
    DB_DSN: str = os.getenv("DB_DSN", "data/watcher.db")
    # logging
    LOG_DIR: str = os.getenv("LOG_DIR", "./logs")
    LOG_FILE: str = os.getenv("LOG_FILE", "bot.log")
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", "7"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


config = Configuration()
