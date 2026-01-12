from enum import Enum
from typing import Optional
import secrets
from application.infrastructure.postgreSQL.models.key import Key


class EnumRole(Enum):
    ADMIN = "admin"
    USER = "user"


def _translit_char(char: str) -> str:
    """
    Простая транслитерация русских букв в латиницу для префиксов ключей.

    Args:
        char: Русская буква в верхнем регистре

    Returns:
        str: Латинская буква или оригинальный символ
    """
    translit_map = {
        "А": "A",
        "Б": "B",
        "В": "V",
        "Г": "G",
        "Д": "D",
        "Е": "E",
        "Ё": "E",
        "Ж": "ZH",
        "З": "Z",
        "И": "I",
        "Й": "Y",
        "К": "K",
        "Л": "L",
        "М": "M",
        "Н": "N",
        "О": "O",
        "П": "P",
        "Р": "R",
        "С": "S",
        "Т": "T",
        "У": "U",
        "Ф": "F",
        "Х": "KH",
        "Ц": "TS",
        "Ч": "CH",
        "Ш": "SH",
        "Щ": "SCH",
        "Ъ": "",
        "Ы": "Y",
        "Ь": "",
        "Э": "E",
        "Ю": "YU",
        "Я": "YA",
    }
    return translit_map.get(char, char)


def generate_key(
    length: Optional[int] = 32,
    name: Optional[str] = None,
    surname: Optional[str] = None,
    role: Optional[EnumRole] = EnumRole.USER,
    telegram_id: Optional[str] = None,
) -> Key:
    """
    Генерация API ключа на основе персональных данных.

    Формат: PREFIX_RANDOMHASH
    Пример: IVK_USER_ABC123DEF456789 или AK_ADMIN_XYZ789UVW123456

    Args:
        length: Длина случайной части ключа
        name: Имя пользователя
        surname: Фамилия пользователя
        role: Роль пользователя

    Returns:
        str: Сгенерированный API ключ
    """
    if length is None:
        length = 32

    prefix = ""
    if name and surname:
        name_first = _translit_char(name[0].upper())
        surname_first = _translit_char(surname[0].upper())
        initials = f"{name_first}{surname_first}"
        prefix = f"{initials}_{role.value.upper()}_"
    elif name:
        name_prefix = "".join(
            _translit_char(c) for c in name[:3].upper() if c.isalpha()
        )
        prefix = f"{name_prefix}_{role.value.upper()}_"
    else:
        prefix = f"{role.value.upper()}_"

    remaining_length = max(16, length - len(prefix))  # Минимум 16 символов случайности
    random_part = secrets.token_hex(remaining_length // 2 + 1)[:remaining_length]

    key_value = f"{prefix}{random_part}"

    return Key(key_value=key_value, active=False, telegram_id=telegram_id)
