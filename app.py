import asyncio, signal

from contextlib import suppress
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.enums import ParseMode
from aiohttp import web

from modules.logger import init_logger
from modules.config import config
from modules.handlers import router
from modules.db.models import init_db
from modules.tracking import start_tracking

logger = init_logger(__name__)


async def on_startup(app: web.Application):
    """
    Runs when the application starts.
    """

    logger.info("Starting the application.")

    # database initialization
    await init_db()

    # setting up webhook if specified
    if config.WEBHOOK_URL:
        await bot.set_webhook(url=config.WEBHOOK_URL)
        logger.info(f"Webhook set to {config.WEBHOOK_URL}")

    # start tracking
    app["tracking"] = asyncio.create_task(start_tracking(bot))
    logger.info("Tracking task started.")


async def on_shutdown(app: web.Application):
    """
    Called when the application terminates.
    """

    logger.info("Shutting down the application...")

    # terminating the background task
    tracking_task = app.get("tracking")
    if tracking_task:
        tracking_task.cancel()
        with suppress(asyncio.CancelledError):
            await tracking_task

    # removing webhook and close session
    if config.WEBHOOK_URL:
        await bot.delete_webhook()
    await bot.session.close()
    logger.info("Bot session closed.")


def setup_signal_handlers(loop: asyncio.AbstractEventLoop):
    """
    Allows to terminate the program gracefully using Ctrl+C (SIGINT, SIGTERM).

    """
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(loop, sig)))


async def shutdown(loop: asyncio.AbstractEventLoop, signal=None):
    """
    Clean shutdown.
    """

    if signal:
        logger.info(f"Received exit signal {signal.name}...")

    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    logger.info(f"Cancelling {len(tasks)} pending tasks...")

    for task in tasks:
        task.cancel()
    with suppress(asyncio.CancelledError):
        await asyncio.gather(*tasks)
    loop.stop()
    logger.info("Shutdown complete.")


async def main():

    # bot cofiguration
    global bot
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )

    dp = Dispatcher()
    dp.include_router(router)

    # webhook mode
    if config.WEBHOOK_URL:
        webapp = web.Application()
        webapp.on_startup.append(on_startup)
        webapp.on_shutdown.append(on_shutdown)

        SimpleRequestHandler(dp, bot).register(webapp, "/webhook")
        setup_application(webapp, dp, bot=bot)

        logger.info(f"Running server on {config.WEBHOOK_HOST}:{config.WEBHOOK_PORT}")
        web.run_app(webapp, host=config.WEBHOOK_HOST, port=config.WEBHOOK_PORT)

    # polling mode
    else:
        logger.info(f"No webhook was specified. Working in polling mode.")
        await init_db()
        asyncio.create_task(start_tracking(bot))

        await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
