"""Обработчик сообщений в режиме чата."""

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..bot_service import ChatBot
from ..states import ChatStates

logger = logging.getLogger(__name__)

messages_router = Router()


def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру главного меню."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 Начать диалог", callback_data="cmd_dialog"
                ),
                InlineKeyboardButton(text="📊 Статус", callback_data="cmd_status"),
            ],
            [
                InlineKeyboardButton(text="🆘 Справка", callback_data="cmd_help"),
                InlineKeyboardButton(text="📚 История", callback_data="cmd_history"),
            ],
        ]
    )
    return keyboard


def create_activation_menu_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру меню активации."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔑 Активировать ключ", callback_data="cmd_activate_info"
                ),
            ],
            [
                InlineKeyboardButton(text="🆘 Справка", callback_data="cmd_help"),
            ],
        ]
    )
    return keyboard


@messages_router.message(ChatStates.dialog_mode, F.text)
async def handle_dialog_message(
    message: Message, state: FSMContext, bot_service: ChatBot
) -> None:
    """
    Обработчик сообщений в режиме RAG-диалога.

    Args:
        message: Сообщение от пользователя
        state: Контекст FSM
        bot_service: Сервис бота
    """
    user_id = message.from_user.id
    user_message = message.text.strip()

    if user_message.lower() in ["выход", "exit", "quit", "Выход"]:
        await bot_service.end_chat(user_id, "по команде пользователя")

        await state.set_state(ChatStates.activated)

        await message.reply(
            "🔚 <b>Диалог завершен</b>\n\n🎯 <b>Выберите следующее действие:</b>",
            parse_mode="HTML",
            reply_markup=create_main_menu_keyboard(),
        )

        logger.info(f"User {user_id} ended dialog with 'выход' command")
        return

    if not user_message:
        await message.reply("❌ Пустое сообщение. Напишите ваш вопрос.")
        return

    user_data = await state.get_data()
    api_key = user_data.get("api_key")
    user_tag = user_data.get("user_tag")

    await bot_service.reset_timer(user_id)

    try:
        await message.bot.send_chat_action(user_id, "typing")
    except TelegramBadRequest:
        logger.warning(f"Could not send typing action to user {user_id}")

    try:
        logger.info(
            f"Sending question to API for user {user_id}: {user_message[:100]}..."
        )

        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key
        if user_tag:
            headers["X-User-Tag"] = user_tag

        chat_history = await bot_service.get_history(user_id, limit=5)

        request_data = {"question": user_message}

        if chat_history:
            history_context = "\n".join(
                [
                    f"Пользователь: {msg['user_message']}\nБот: {msg['bot_response']}"
                    for msg in chat_history[-3:]
                ]
            )
            request_data["history_context"] = history_context

        response = await bot_service.api_client.client.post(
            f"{bot_service.api_client.config.api_base_url}/v1/chat",
            json=request_data,
            headers=headers,
        )

        response.raise_for_status()
        response_data = response.json()

        bot_response = response_data.get(
            "answer", "Извините, не удалось получить ответ."
        )

        await message.reply(bot_response)

        await bot_service.add_to_history(user_id, user_message, bot_response)

        sources = response_data.get("sources", [])
        if sources:
            sources_text = "\n\n📚 <b>Источники информации:</b>\n"
            for i, src in enumerate(sources[:5], 1):
                filename = src.get("metadata", {}).get("filename", "Неизвестно")
                sources_text += f"{i}. {filename}\n"

            sources_text += "\n💡 <i>Если хотите посмотреть выдержку из документа, напишите номер источника (1-5)</i>"

            await state.update_data(last_sources=sources)

            await message.reply(sources_text, parse_mode="HTML")

        logger.info(f"Successfully responded to user {user_id}")

    except Exception as e:
        logger.error(f"Error processing message from user {user_id}: {e}")

        error_message = (
            "❌ Извините, произошла ошибка при обработке вашего запроса.\n\n"
            f"Детали: {str(e)}\n\n"
            "Попробуйте переформулировать вопрос или используйте /end для завершения диалога."
        )

        await message.reply(error_message)


@messages_router.message(ChatStates.dialog_mode, F.text.regexp(r"^[1-5]$"))
async def handle_source_selection(message: Message, state: FSMContext) -> None:
    """
    Обработчик выбора источника для просмотра выдержки.
    """
    user_id = message.from_user.id
    source_number = int(message.text.strip()) - 1

    user_data = await state.get_data()
    sources = user_data.get("last_sources", [])

    if not sources or source_number >= len(sources):
        await message.reply(
            "❌ <b>Неверный номер источника</b>\n\n"
            "Пожалуйста, выберите номер от 1 до 5 из списка источников.",
            parse_mode="HTML",
        )
        return

    selected_source = sources[source_number]

    filename = selected_source.get("metadata", {}).get("filename", "Неизвестно")
    content = selected_source.get("content", "Содержимое недоступно")

    excerpt = content[:1000] + "..." if len(content) > 1000 else content

    response_text = (
        f"📄 <b>Выдержка из документа: {filename}</b>\n\n"
        f"{excerpt}\n\n"
        "💡 <i>Задайте новый вопрос или выберите другой источник</i>"
    )

    await message.reply(response_text, parse_mode="HTML")

    logger.info(f"User {user_id} requested excerpt from source {source_number + 1}")


@messages_router.message(ChatStates.timeout_warning, F.text)
async def handle_timeout_warning_message(
    message: Message, state: FSMContext, bot_service: ChatBot
) -> None:
    """
    Обработчик сообщений во время предупреждения о таймауте.

    Сообщение переводит пользователя обратно в диалог.
    """
    user_id = message.from_user.id

    await state.set_state(ChatStates.dialog_mode)

    await bot_service.reset_timer(user_id)

    await message.reply("✅ Диалог продолжен!\n\nТаймер бездействия сброшен.")

    await handle_dialog_message(message, state, bot_service)


@messages_router.message(ChatStates.idle)
async def handle_idle_message(message: Message) -> None:
    """Обработчик сообщений в состоянии idle."""
    await message.reply(
        "🤖 Используйте /start для начала работы\n\n"
        "Доступные команды:\n"
        "/start - запустить бота\n"
        "/help - справка"
    )


@messages_router.message(ChatStates.waiting_for_activation)
async def handle_waiting_activation_message(message: Message) -> None:
    """Обработчик неожиданных сообщений при ожидании активации."""
    await message.reply(
        "🔑 <b>Требуется активация API ключа</b>\n\n"
        "Используйте /activate &lt;ключ&gt; или выберите действие:",
        parse_mode="HTML",
        reply_markup=create_activation_menu_keyboard(),
    )


@messages_router.message(ChatStates.activated)
async def handle_activated_message(message: Message) -> None:
    """Обработчик сообщений в состоянии activated (главное меню)."""
    await message.reply(
        "🎯 <b>Главное меню</b>\n\nВыберите действие или отправьте команду:",
        parse_mode="HTML",
        reply_markup=create_main_menu_keyboard(),
    )


@messages_router.message(ChatStates.closed)
async def handle_closed_message(message: Message, state: FSMContext) -> None:
    """Обработчик сообщений в состоянии closed."""
    await message.reply(
        "🔚 Диалог завершен.\n\nИспользуйте /start для перезапуска бота."
    )

    await state.set_state(ChatStates.idle)
