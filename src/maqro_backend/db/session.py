from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from maqro_backend.core.config import settings
from maqro_backend.db.base import Base  


engine = create_async_engine(settings.database_url)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()