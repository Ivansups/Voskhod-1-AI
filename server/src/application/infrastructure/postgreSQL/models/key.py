from sqlalchemy import Column, String, Integer, DateTime, Boolean, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from .base import Base


class Key(Base):
    """SQLAlchemy модель для API ключа."""

    __tablename__ = "keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_value = Column(String(64), unique=True, nullable=False, index=True)
    active = Column(Boolean, default=True, nullable=True)
    telegram_id = Column(String(50), nullable=True, index=True)
    tag = Column(String(100), nullable=True, index=True)
    count_requests = Column(Integer, default=0, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)


async def verify_api_key(db: AsyncSession, api_key: str, user_tag: str = None) -> bool:
    """
    Проверка API ключа с проверкой принадлежности пользователя.

    Новая логика проверки:
    1. Запрос в БД - Есть ли такой ключ?
    2. Если ключа нет - доступ запрещен
    3. Если ключ найден и active=True и tag совпадает с user_tag - доступ разрешен, увеличиваем счетчик
    4. Если ключ найден но tag не совпадает - доступ запрещен
    5. Если ключ найден и active=False - доступ запрещен

    Args:
        db: Асинхронная сессия базы данных
        api_key: API ключ для проверки
        user_tag: Тег пользователя для проверки принадлежности

    Returns:
        bool: True если доступ разрешен, False если запрещен
    """
    try:
        if user_tag:
            user_tag = user_tag.lstrip("@")

        stmt = select(Key).where(Key.key_value == api_key)
        result = await db.execute(stmt)
        key = result.scalar_one_or_none()

        if key is None:
            return False

        if key.active and key.tag == user_tag:
            key.count_requests += 1
            await db.commit()
            return True
        else:
            return False

    except Exception as e:
        print(f"Error verifying API key: {e}")
        return False
