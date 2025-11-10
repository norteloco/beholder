import asyncio, aiohttp

from aiogram import Bot, html

from modules.config import config
from modules.db.requests import get_all_trackings, update_tracking_version
from modules.logger import init_logger
from modules.providers import Provider

logger = init_logger(__name__)


async def process_tracking_item(bot: Bot, session: aiohttp.ClientSession, item):
    """
    Processing one track.
    """
    try:
        provider_cls = next(
            (p for p in Provider.registry if p.name == item.provider), None
        )
        if not provider_cls:
            logger.warning(f"Unknown provider {item.provider} for {item.fullname}.")
            return

        latest = await provider_cls.fetch_latest(session, item.namespace, item.repository)  # type: ignore
        if not latest:
            logger.debug(f"No new version found for {item.fullname}.")
            return

        if item.version != latest:
            logger.info(
                f"{item.provider}: Found new version for {item.fullname}: {latest}"
            )
            await update_tracking_version(item.id, latest)

            message = (
                f'{html.bold("🔔New release!")}\n'
                f'{html.link(f"{item.repository}/{item.namespace}", item.url)}\n'
                f"Version: {latest}\n"
                f"Link: {item.url}\n"
            )

            try:
                await bot.send_message(item.chat_id, message)
                logger.info(f"Notification sent to chat {item.chat_id}")
            except Exception as e:
                logger.exception(f"Failed to send notification: {e}")

        else:
            logger.debug(f"No updates for {item.fullname} (current: {item.version})")

    except Exception as e:
        logger.exception(
            f"Error processing {item.provider}: {item.fullname}. Error message: {e}"
        )


async def start_tracking(bot: Bot):
    """
    Main version monitoring cycle.
    """

    logger.info(f"Tracking started with interval {config.POLL_INTERVAL} seconds.")

    async with aiohttp.ClientSession() as session:
        while session:
            try:
                trackings = await get_all_trackings()
                if not trackings:
                    logger.info("No tracked repositories found")
                    await asyncio.sleep(config.POLL_INTERVAL)
                    continue
                logger.info(f"Found {len(trackings)} traced repositories.")

                tasks = [
                    asyncio.create_task(process_tracking_item(bot, session, item))
                    for item in trackings
                ]
                await asyncio.gather(*tasks)

            except Exception as e:
                logger.exception(f"Global tracking loop error: {e}")

            logger.info(f"Sleeping for {config.POLL_INTERVAL} seconds.")
            await asyncio.sleep(config.POLL_INTERVAL)
