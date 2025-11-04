from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from modules.logger import init_logger
from modules.config import config

logger = init_logger(__name__)
engine = create_async_engine(url=f"sqlite+aiosqlite:///{config.DB_DSN}")
if engine:
    logger.debug(f"Engine created: {engine.url}")
else:
    logger.error(
        f"Failed to create engine. Please check the configuration and restart the application."
    )
    SystemExit()

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Chat(Base):
    __tablename__ = "chats"
    chat_id = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class Tracking(Base):
    __tablename__ = "trackings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id = mapped_column(BigInteger, ForeignKey("chats.chat_id"))
    provider: Mapped[str] = mapped_column(String(10))
    namespace: Mapped[str] = mapped_column(String(255))
    repository: Mapped[str] = mapped_column(String(255))
    fullname: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    version: Mapped[str | None] = mapped_column(nullable=True)

async def db_init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
