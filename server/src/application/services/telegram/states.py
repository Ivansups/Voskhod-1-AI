"""Состояния FSM для телеграм бота."""

from aiogram.fsm.state import State, StatesGroup


class ChatStates(StatesGroup):
    """Состояния диалога с пользователем."""

    idle = State()  # Ожидание команд (/start, /help)
    waiting_for_activation = State()  # Ожидание команды /activate <ключ>
    activated = State()  # Ключ активирован, главное меню
    dialog_mode = State()  # RAG-диалог активен
    timeout_warning = State()  # Предупреждение о скором завершении
    closed = State()  # Диалог завершен
