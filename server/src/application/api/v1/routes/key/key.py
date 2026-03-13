from datetime import datetime
from typing import Optional

from application.api.deps import get_db, verify_api_key_dependency
from application.infrastructure.postgreSQL.models.key import Key
from application.services.key_generator.key_gen import EnumRole, generate_key
from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["keys"])


class KeyResponse(BaseModel):
    """Pydantic модель для ответа с информацией о ключе."""

    id: str
    key_value: str
    active: bool
    telegram_id: Optional[str]
    tag: Optional[str]
    count_requests: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Конвертация из SQLAlchemy модели с правильной обработкой UUID."""
        data = {
            "id": str(obj.id),
            "key_value": obj.key_value,
            "active": obj.active,
            "telegram_id": obj.telegram_id,
            "tag": obj.tag,
            "count_requests": obj.count_requests,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        return cls(**data)


@router.post("/keys", description="Создание нового ключа с привязкой к Telegram ID")
async def create_key(
    db: AsyncSession = Depends(get_db),
    name: Optional[str] = Form(None),
    surname: Optional[str] = Form(None),
    role: str = Form("user"),
    telegram_id: Optional[str] = Form(None),
) -> KeyResponse:
    """
    Создает API ключ с привязкой к конкретному Telegram ID.

    Args:
        name: Имя студента
        surname: Фамилия студента
        role: Роль (user/admin)
        telegram_id: Telegram ID студента (обязательно для user)

    Returns:
        Созданный ключ
    """
    if role.lower() == "user" and not telegram_id:
        raise HTTPException(
            status_code=400, detail="telegram_id обязателен для пользователей"
        )

    role_enum = EnumRole.USER if role.lower() == "user" else EnumRole.ADMIN

    key = generate_key(
        name=name, surname=surname, role=role_enum, telegram_id=telegram_id
    )

    db.add(key)
    await db.commit()
    await db.refresh(key)

    return KeyResponse.from_orm(key)


@router.get("/keys", description="Получение всех ключей (требуется аутентификация)")
async def get_keys(
    _: None = Depends(verify_api_key_dependency), db: AsyncSession = Depends(get_db)
) -> list[KeyResponse]:
    result = await db.execute(select(Key).order_by(Key.created_at.desc()))
    keys = result.scalars().all()
    return [KeyResponse.from_orm(key) for key in keys]


@router.get(
    "/keys/{key_id}", description="Получение ключа по его ID (требуется аутентификация)"
)
async def get_key(
    key_id: str,
    _: None = Depends(verify_api_key_dependency),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Key).where(Key.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return KeyResponse.from_orm(key)


@router.post(
    "/keys/verify",
    description="Проверка и активация API ключа с привязкой к Telegram ID",
)
async def verify_key_only(
    key_value: str, user_tag: str = None, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Проверяет API ключ и активирует его если он предназначен для данного Telegram ID.
    """
    if user_tag:
        user_tag = user_tag.lstrip("@")

    result = await db.execute(select(Key).where(Key.key_value == key_value))
    key = result.scalar_one_or_none()

    if not key:
        return {"valid": False, "error": "Key not found"}

    if key.telegram_id and key.telegram_id != user_tag:
        return {
            "valid": False,
            "error": "Key is assigned to another Telegram user",
            "assigned_to": key.telegram_id,
        }

    if not key.active:
        key.active = True
        key.tag = user_tag
        await db.commit()
        await db.refresh(key)

        return {
            "valid": True,
            "activated": True,
            "key_id": str(key.id),
            "owner": f"{key.key_value.split('_')[0] if '_' in key.key_value else 'Unknown'}",
            "created_at": key.created_at.isoformat() if key.created_at else None,
            "telegram_id": key.telegram_id,
            "user_tag": user_tag,
        }
    else:
        if key.tag == user_tag:
            return {
                "valid": True,
                "activated": False,  # Уже был активирован этим пользователем
                "key_id": str(key.id),
                "owner": f"{key.key_value.split('_')[0] if '_' in key.key_value else 'Unknown'}",
                "telegram_id": key.telegram_id,
                "user_tag": key.tag,
            }
        else:
            return {
                "valid": False,
                "error": "Key already activated by another user",
                "key_id": str(key.id),
                "owner": f"{key.key_value.split('_')[0] if '_' in key.key_value else 'Unknown'}",
                "current_owner_tag": key.tag,
            }


@router.post(
    "/keys/check_activation", description="Проверка активации ключа пользователя"
)
async def check_user_activation(
    user_tag: str, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Проверяет, есть ли у пользователя активированный ключ.

    Args:
        user_tag: Тег пользователя

    Returns:
        dict: Информация об активации
    """
    user_tag = user_tag.lstrip("@")

    result = await db.execute(select(Key).where(Key.tag == user_tag, Key.active))
    key = result.scalar_one_or_none()

    if key:
        return {
            "has_activated_key": True,
            "key_id": str(key.id),
            "created_at": key.created_at.isoformat() if key.created_at else None,
        }
    else:
        return {"has_activated_key": False}


@router.delete(
    "/keys/{key_id}", description="Удаление ключа по его ID (требуется аутентификация)"
)
async def delete_key(
    key_id: str,
    _: None = Depends(verify_api_key_dependency),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Key).where(Key.id == key_id))
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    await db.delete(key)
    await db.commit()

    return {"message": "Ключ успешно удален"}
