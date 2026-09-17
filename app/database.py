from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:senha@localhost/escola_db",
)

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
