from sqlalchemy import select, delete, update

from modules.logger import init_logger
from modules.db.models import async_session
from modules.db.models import Chat, Tracking

logger = init_logger(__name__)


# chats table
async def add_chat(chat_id: int):
    async with async_session() as session:
        chat = await session.scalar(select(Chat).where(Chat.chat_id == chat_id))
        if not chat:
            session.add(Chat(chat_id=chat_id))
            await session.commit()
            logger.debug(
                f"Table {Chat.__tablename__}: New record has been added to the database."
            )
        else:
            logger.debug(
                f"Table {Chat.__tablename__}: There is already a record in the database."
            )


async def del_chat(chat_id: int):
    async with async_session() as session:
        chat = await session.scalar(select(Chat).where(Chat.chat_id == chat_id))

        if chat:
            await session.delete(Chat(chat_id=chat_id))
            await session.commit()
            logger.debug(
                f"Table {Chat.__tablename__}: Record has been removed from the database."
            )
        else:
            logger.debug(
                f"Table {Chat.__tablename__}: Could not find a database record to delete."
            )


# trackings table
async def add_tracking(
    chat_id: int,
    provider: str,
    namespace: str,
    repository: str,
    fullname: str,
    url: str,
):
    async with async_session() as session:
        tracking = await session.scalar(
            select(Tracking).where(
                (Tracking.chat_id == chat_id)
                & (Tracking.provider == provider)
                & (Tracking.fullname == fullname)
            )
        )

        if not tracking:
            session.add(
                Tracking(
                    chat_id=chat_id,
                    provider=provider,
                    namespace=namespace,
                    repository=repository,
                    fullname=fullname,
                    url=url,
                )
            )
            await session.commit()
            logger.debug(
                f"Table {Tracking.__tablename__}: New record has been added to the database."
            )
        else:
            logger.debug(
                f"Table {Tracking.__tablename__}: There is already a record in the database."
            )


async def del_tracking(track_id: int):
    async with async_session() as session:
        track = await session.scalar(select(Tracking).where(Tracking.id == track_id))
        if track:
            await session.execute(delete(Tracking).where(Tracking.id == track.id))
            await session.commit()
            logger.debug(
                f"Table {Tracking.__tablename__}: Record has been removed from the database."
            )
        else:
            logger.debug(
                f"Table {Tracking.__tablename__}: Could not find a database record to delete."
            )


async def get_tracking(track_id: int):
    async with async_session() as session:
        track = await session.scalar(select(Tracking).where(Tracking.id == track_id))
        if track:
            return track
        else:
            logger.debug(
                f"Table {Tracking.__tablename__}: Unable to find record in database."
            )
            return None


async def get_chat_trackings(chat_id: int):
    async with async_session() as session:
        tracks = await session.scalars(
            select(Tracking).where(Tracking.chat_id == chat_id)
        )
        if tracks:
            return tracks.all()
        else:
            logger.debug(
                f"Table {Tracking.__tablename__}: Unable to find record in database."
            )
            return None


async def get_all_trackings():
    async with async_session() as session:
        tracks = await session.scalars(select(Tracking))
        if tracks:
            return tracks.all()
        else:
            logger.debug(
                f"Table {Tracking.__tablename__}: Unable to find any record in database."
            )
            return None


# version update
async def update_tracking_version(track_id: int, version: str):
    async with async_session() as session:
        await session.execute(
            update(Tracking).where(Tracking.id == track_id).values(version=version)
        )
        await session.commit()
