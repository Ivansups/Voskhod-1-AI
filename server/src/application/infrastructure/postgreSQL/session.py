from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .models.base import Base
from application.core.config import settings

async_url = settings.POSTGRES_URL

engine = create_async_engine(
    async_url, echo=False, future=True, pool_pre_ping=True, pool_recycle=300
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Асинхронная зависимость для получения сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Создание всех таблиц (для разработки)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Удаление всех таблиц (для тестирования)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
