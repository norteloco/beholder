import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from modules.config import config


def init_logger(name: str | None = None) -> logging.Logger:

    # log file configuration
    log_dir = Path(config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / config.LOG_FILE

    # logger init
    if name:
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger()

    # level
    log_level = getattr(logging, config.LOG_LEVEL, logging.INFO)

    # formatter
    log_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )

    # handlers
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        backupCount=config.LOG_RETENTION_DAYS,
        encoding="UTF-8",
    )

    console_handler = logging.StreamHandler()

    file_handler.setFormatter(log_formatter)
    console_handler.setFormatter(log_formatter)
    logger.handlers.clear()

    # apply logger configuration
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # reducing aiogram noise
    logging.getLogger("aiogram").setLevel(logging.WARNING)

    return logger
