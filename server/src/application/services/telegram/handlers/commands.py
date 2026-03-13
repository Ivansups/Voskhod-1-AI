"""Обработчики команд телеграм бота."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..bot_service import ChatBot
from ..states import ChatStates

logger = logging.getLogger(__name__)

# Создаем роутер для команд
commands_router = Router()


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


def create_help_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру справки."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd_start"),
            ]
        ]
    )
    return keyboard


@commands_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, bot_service: ChatBot) -> None:
    """Обработчик команды /start."""
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    user_tag = username

    activation_result = await bot_service.check_user_activation(user_tag)
    has_activated_key = (
        activation_result.get("has_activated_key", False)
        if isinstance(activation_result, dict)
        else activation_result
    )

    logger.info(
        f"User {user_id} ({user_tag}) activation check result: {activation_result}, has_activated_key: {has_activated_key}"
    )

    if has_activated_key:
        await state.set_state(ChatStates.activated)
        await state.update_data(user_tag=user_tag)

        welcome_text = (
            f"👋 Привет, {username}!\n\n"
            "✅ <b>У вас есть активированный API ключ</b>\n\n"
            "🎯 <b>Выберите действие:</b>"
        )
        keyboard = create_main_menu_keyboard()
    else:
        await state.set_state(ChatStates.waiting_for_activation)

        welcome_text = (
            f"👋 Привет, {username}!\n\n"
            "🔑 <b>Для использования бота требуется активация API ключа</b>\n\n"
            "<i>Получите API ключ у администратора университета</i>"
        )
        keyboard = create_activation_menu_keyboard()

    await message.reply(welcome_text, parse_mode="HTML", reply_markup=keyboard)
    logger.info(f"User {user_id} started bot, activation status: {has_activated_key}")


@commands_router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    """Обработчик команды /help."""
    current_state = await state.get_state()

    if current_state == ChatStates.waiting_for_activation:
        help_text = (
            "🆘 <b>Справка - Режим активации</b>\n\n"
            "🔑 <b>Для использования бота требуется активация API ключа</b>\n\n"
            "📝 <b>Команды:</b>\n"
            "/start - перезапустить бота\n"
            "/activate &lt;ключ&gt; - активировать API ключ\n"
            "/help - показать эту справку\n\n"
            "💡 <b>Как активировать:</b>\n"
            "1. Получите API ключ у администратора\n"
            "2. Напишите /activate ABC123_DEF456\n"
            "3. Начните диалог командой /dialog"
        )
    elif current_state == ChatStates.activated:
        help_text = (
            "🆘 <b>Справка - Главное меню</b>\n\n"
            "✅ <b>Ваш ключ активирован</b>\n\n"
            "📝 <b>Команды:</b>\n"
            "/start - перезапустить бота\n"
            "/dialog - начать диалог\n"
            "/status - статус активации\n"
            "/help - показать эту справку\n\n"
            "💡 <b>Как пользоваться:</b>\n"
            "1. Напишите /dialog\n"
            "2. Задайте свой вопрос\n"
            "3. Получите ответ с источниками\n"
            "4. Выберите источник для просмотра выдержки"
        )
    elif current_state == ChatStates.dialog_mode:
        help_text = (
            "🆘 <b>Справка - Режим диалога</b>\n\n"
            "🎯 <b>Вы в режиме диалога</b>\n\n"
            "📝 <b>Команды:</b>\n"
            "/end - завершить диалог\n"
            "/help - показать эту справку\n\n"
            "💡 <b>Как пользоваться:</b>\n"
            "1. Задайте вопрос в свободной форме\n"
            "2. Получите ответ\n"
            "3. При наличии источников выберите номер (1-5) для просмотра выдержки\n"
            "4. Напишите 'выход' для завершения диалога\n\n"
            "⏰ <b>Важно:</b> Диалог завершится через 3 минуты бездействия"
        )
    else:
        help_text = (
            "🆘 <b>Справка по командам:</b>\n\n"
            "📝 <b>Основные команды:</b>\n"
            "/start - запустить бота и проверить активацию\n"
            "/activate &lt;ключ&gt; - активировать API ключ\n"
            "/dialog - начать диалог\n"
            "/status - статус активации\n"
            "/help - показать эту справку\n"
            "/history - история сообщений\n"
            "/end - завершить диалог\n\n"
            "💡 <b>Алгоритм работы:</b>\n"
            "1. /start - проверка активации\n"
            "2. /activate &lt;ключ&gt; - если не активирован\n"
            "3. /dialog - начало общения\n"
            "4. Вопрос → Ответ с источниками → Выбор источника"
        )

    keyboard = (
        create_main_menu_keyboard()
        if current_state in [ChatStates.activated, ChatStates.dialog_mode]
        else create_activation_menu_keyboard()
        if current_state == ChatStates.waiting_for_activation
        else create_help_keyboard()
    )
    await message.reply(help_text, parse_mode="HTML", reply_markup=keyboard)


@commands_router.message(Command("chat"), ChatStates.idle)
async def cmd_chat(message: Message, state: FSMContext) -> None:
    """Обработчик команды /chat - запрос API ключа."""
    user_id = message.from_user.id

    # Меняем состояние на ожидание ключа
    await state.set_state(ChatStates.waiting_for_activation)

    await message.reply(
        "🔑 <b>Для начала диалога требуется API ключ</b>\n\n"
        "Пожалуйста, введите ваш API ключ для доступа к системе:\n\n"
        "<i>Ключ можно получить у администратора университета</i>\n\n"
        "Если у вас нет ключа, обратитесь к преподавателю или администратору.",
        parse_mode="HTML",
    )

    logger.info(f"User {user_id} initiated chat, waiting for API key")


@commands_router.message(Command("chat"))
async def cmd_chat_wrong_state(message: Message) -> None:
    """Обработчик команды /chat в неправильном состоянии."""
    await message.reply(
        "❌ Вы уже в процессе ввода ключа или в диалоге!\n\n"
        "Если хотите начать заново, используйте /end чтобы завершить текущий процесс."
    )


@commands_router.message(Command("end"), ChatStates.dialog_mode)
async def cmd_end_dialog(
    message: Message, state: FSMContext, bot_service: ChatBot
) -> None:
    """Обработчик команды /end - завершить RAG-диалог."""
    user_id = message.from_user.id

    await bot_service.end_chat(user_id, "по команде пользователя")

    # Меняем состояние на activated (главное меню)
    await state.set_state(ChatStates.activated)

    await message.reply(
        "🔚 <b>Диалог завершен</b>\n\n🎯 <b>Выберите следующее действие:</b>",
        parse_mode="HTML",
        reply_markup=create_main_menu_keyboard(),
    )

    logger.info(f"User {user_id} ended dialog manually")


@commands_router.message(Command("end"), ChatStates.timeout_warning)
async def cmd_end_timeout(
    message: Message, state: FSMContext, bot_service: ChatBot
) -> None:
    """Обработчик команды /end во время предупреждения о таймауте."""
    user_id = message.from_user.id

    await bot_service.end_chat(user_id, "по команде пользователя")

    # Меняем состояние на activated
    await state.set_state(ChatStates.activated)

    logger.info(f"User {user_id} ended dialog during timeout warning")


@commands_router.message(Command("end"), ChatStates.waiting_for_activation)
async def cmd_end_waiting_key(message: Message, state: FSMContext) -> None:
    """Обработчик команды /end при ожидании ввода ключа."""
    user_id = message.from_user.id

    # Возвращаемся в idle состояние
    await state.set_state(ChatStates.idle)
    await state.update_data(api_key=None)  # Очищаем данные

    await message.reply(
        "🔚 <b>Ввод ключа отменен</b>\n\n"
        "Вы вернулись в главное меню.\n"
        "Используйте /chat чтобы попробовать снова.",
        parse_mode="HTML",
    )

    logger.info(f"User {user_id} cancelled key input")


@commands_router.message(Command("end"))
async def cmd_end_wrong_state(message: Message) -> None:
    """Обработчик команды /end в неправильном состоянии."""
    await message.reply(
        "❌ Нет активного процесса для завершения.\n\n"
        "Используйте /chat чтобы начать диалог."
    )


@commands_router.message(Command("activate"))
async def cmd_activate(
    message: Message, state: FSMContext, bot_service: ChatBot
) -> None:
    """Обработчик команды /activate <ключ>."""
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    user_tag = username

    command_parts = message.text.split()
    if len(command_parts) < 2:
        await message.reply(
            "❌ <b>Ошибка формата команды</b>\n\n"
            "Используйте: /activate &lt;Ключ&gt;\n\n"
            "<i>Пример: /activate ABC123_DEF456</i>",
            parse_mode="HTML",
        )
        return

    api_key = command_parts[1].strip()

    status_message = await message.reply("🔍 Активирую ключ...")
    await message.bot.send_chat_action(user_id, "typing")

    try:
        verification_result = await bot_service.verify_api_key(api_key, user_tag)

        if verification_result.get("valid") and verification_result.get("activated"):
            await state.set_state(ChatStates.activated)
            await state.update_data(user_tag=user_tag, api_key=api_key)

            await status_message.delete()

            await message.reply(
                "✅ <b>Ключ успешно активирован!</b>\n\n"
                "🎯 <b>Теперь доступны следующие действия:</b>",
                parse_mode="HTML",
                reply_markup=create_main_menu_keyboard(),
            )

            logger.info(f"User {user_id} successfully activated key")

        elif verification_result.get("valid") and not verification_result.get(
            "activated"
        ):
            await state.set_state(ChatStates.activated)
            await state.update_data(user_tag=user_tag, api_key=api_key)

            await status_message.delete()

            await message.reply(
                "✅ <b>Ключ уже активирован вами ранее</b>\n\n"
                "🎯 <b>Доступны действия:</b>",
                parse_mode="HTML",
                reply_markup=create_main_menu_keyboard(),
            )

            logger.info(f"User {user_id} key was already activated")

        else:
            await status_message.delete()

            error_msg = "❌ <b>Не удалось активировать ключ</b>\n\n"

            if (
                verification_result.get("error")
                == "Key already activated by another user"
            ):
                error_msg += "Этот ключ уже активирован другим пользователем.\n\n"
                error_msg += "<i>Пожалуйста, получите новый ключ у администратора</i>"
            elif verification_result.get("error") == "Key not found":
                error_msg += "Ключ не найден в системе.\n\n"
                error_msg += "<i>Проверьте правильность ввода или обратитесь к администратору</i>"
            else:
                error_msg += f"Ошибка: {verification_result.get('error', 'Неизвестная ошибка')}\n\n"
                error_msg += "<i>Попробуйте еще раз или обратитесь к администратору</i>"

            await message.reply(error_msg, parse_mode="HTML")
            logger.warning(
                f"User {user_id} failed to activate key: {verification_result}"
            )

    except Exception as e:
        await status_message.delete()
        logger.error(f"Error activating key for user {user_id}: {e}")

        await message.reply(
            "❌ <b>Ошибка активации ключа</b>\n\n"
            f"Детали: {str(e)}\n\n"
            "Попробуйте еще раз или обратитесь к администратору.",
            parse_mode="HTML",
        )


@commands_router.message(Command("dialog"))
async def cmd_dialog(message: Message, state: FSMContext, bot_service: ChatBot) -> None:
    """Обработчик команды /dialog - начать диалог."""
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    user_data = await state.get_data()
    user_tag = user_data.get("user_tag") or username

    if not user_data.get("user_tag"):
        await state.update_data(user_tag=user_tag)

    activation_result = await bot_service.check_user_activation(
        user_tag.replace("@", "")
    )
    has_activated_key = (
        activation_result.get("has_activated_key", False)
        if isinstance(activation_result, dict)
        else activation_result
    )
    if not has_activated_key:
        await state.set_state(ChatStates.waiting_for_activation)
        await message.reply(
            "🔑 <b>Для использования диалога требуется активация ключа</b>\n\n"
            "📝 <b>Доступные команды:</b>\n"
            "/activate &lt;ключ&gt; - активировать ключ\n"
            "/help - справка\n\n"
            "<i>Получите API ключ у администратора университета</i>",
            parse_mode="HTML",
        )
        return

    current_state = await state.get_state()
    if current_state == ChatStates.dialog_mode:
        await message.reply(
            "🎯 <b>Диалог уже активен!</b>\n\n"
            "Задавайте свои вопросы или используйте /end для завершения.",
            parse_mode="HTML",
        )
        return

    await state.set_state(ChatStates.dialog_mode)

    await bot_service.start_inactivity_timer(user_id)

    await message.reply(
        "🎯 <b>Диалог начат!</b>\n\n"
        "Теперь вы можете задавать вопросы. "
        "Я буду искать ответы в учебных материалах университета.\n\n"
        "Напишите ваш вопрос или используйте меню для управления.",
        parse_mode="HTML",
        reply_markup=create_main_menu_keyboard(),
    )

    logger.info(f"User {user_id} started dialog")


@commands_router.message(Command("status"), ChatStates.activated)
async def cmd_status(message: Message, state: FSMContext, bot_service: ChatBot) -> None:
    """Обработчик команды /status - показать статус активации."""
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    user_data = await state.get_data()
    user_tag = user_data.get("user_tag") or username

    if not user_tag:
        await message.reply(
            "❌ <b>Ошибка: пользователь не идентифицирован</b>", parse_mode="HTML"
        )
        return

    try:
        activation_info = await bot_service.check_user_activation(
            user_tag.replace("@", "")
        )

        if activation_info.get("has_activated_key"):
            status_text = (
                "📊 <b>Статус активации:</b>\n\n"
                "✅ <b>Ключ активирован</b>\n"
                f"🆔 ID ключа: {activation_info.get('key_id', 'N/A')}\n"
                f"📅 Активирован: {activation_info.get('created_at', 'N/A')}\n\n"
                "🎯 <b>Доступные действия:</b>\n"
                "/dialog - начать диалог\n"
                "/help - справка"
            )
        else:
            status_text = (
                "📊 <b>Статус активации:</b>\n\n"
                "❌ <b>Ключ не активирован</b>\n\n"
                "Используйте /activate &lt;ключ&gt; для активации"
            )

        await message.reply(
            status_text, parse_mode="HTML", reply_markup=create_main_menu_keyboard()
        )

    except Exception as e:
        logger.error(f"Error getting status for user {user_id}: {e}")
        await message.reply(
            f"❌ <b>Ошибка получения статуса</b>\n\nДетали: {str(e)}", parse_mode="HTML"
        )


@commands_router.message(Command("status"))
async def cmd_status_wrong_state(message: Message) -> None:
    """Обработчик команды /status в неправильном состоянии."""
    await message.reply(
        "❌ Сначала активируйте ключ командой /activate &lt;ключ&gt;",
        parse_mode="HTML",
    )


@commands_router.message(Command("history"))
async def cmd_history(message: Message, bot_service: ChatBot) -> None:
    """Обработчик команды /history - показать историю."""
    user_id = message.from_user.id

    history = await bot_service.get_history(user_id)

    if not history:
        await message.reply(
            "📝 История сообщений пуста.\n\nНачните диалог с помощью /dialog"
        )
        return

    history_text = "📚 <b>История диалога:</b>\n\n"

    for i, entry in enumerate(history[-10:], 1):
        history_text += f"{i}. <b>Вы:</b> {entry['user_message'][:100]}{'...' if len(entry['user_message']) > 100 else ''}\n"
        history_text += f"   <b>Бот:</b> {entry['bot_response'][:100]}{'...' if len(entry['bot_response']) > 100 else ''}\n\n"

    if len(history) > 10:
        history_text += f"Показаны последние 10 из {len(history)} сообщений."

    await message.reply(
        history_text, parse_mode="HTML", reply_markup=create_main_menu_keyboard()
    )

    logger.info(f"User {user_id} requested history ({len(history)} messages)")


# Обработчики callback-запросов от кнопок
@commands_router.callback_query(F.data == "cmd_dialog")
async def callback_dialog(
    callback: CallbackQuery, state: FSMContext, bot_service: ChatBot
) -> None:
    """Обработчик кнопки 'Начать диалог'."""
    user_id = callback.from_user.id
    username = callback.from_user.username or f"user_{user_id}"
    user_data = await state.get_data()
    user_tag = user_data.get("user_tag") or username

    if not user_data.get("user_tag"):
        await state.update_data(user_tag=user_tag)

    activation_result = await bot_service.check_user_activation(
        user_tag.replace("@", "")
    )
    has_activated_key = (
        activation_result.get("has_activated_key", False)
        if isinstance(activation_result, dict)
        else activation_result
    )
    if not has_activated_key:
        await callback.message.edit_text(
            "🔑 <b>Для использования диалога требуется активация ключа</b>\n\n"
            "<i>Получите ключ у администратора университета</i>",
            parse_mode="HTML",
            reply_markup=create_activation_menu_keyboard(),
        )
        return

    current_state = await state.get_state()
    if current_state == ChatStates.dialog_mode:
        # Не редактируем сообщение, если оно уже содержит нужный текст
        try:
            await callback.answer("Диалог уже активен!")
        except Exception:
            pass  # Игнорируем ошибки callback.answer
        return

    await state.set_state(ChatStates.dialog_mode)
    await bot_service.start_inactivity_timer(user_id)

    try:
        await callback.message.edit_text(
            "🎯 <b>Диалог начат!</b>\n\n"
            "Теперь вы можете задавать вопросы. "
            "Я буду искать ответы в учебных материалах университета.\n\n"
            "Напишите ваш вопрос или нажмите /end чтобы завершить диалог.",
            parse_mode="HTML",
            reply_markup=create_main_menu_keyboard(),
        )
    except Exception:
        # Если редактирование не удалось (например, контент не изменился), просто отвечаем
        await callback.answer("Диалог уже начат!")

    await callback.answer()

    logger.info(f"User {user_id} started dialog via button")


@commands_router.callback_query(F.data == "cmd_status")
async def callback_status(
    callback: CallbackQuery, state: FSMContext, bot_service: ChatBot
) -> None:
    """Обработчик кнопки 'Статус'."""
    user_id = callback.from_user.id
    username = callback.from_user.username or f"user_{user_id}"
    user_data = await state.get_data()
    user_tag = user_data.get("user_tag") or username

    if not user_tag:
        await callback.message.edit_text(
            "❌ <b>Ошибка: пользователь не идентифицирован</b>",
            parse_mode="HTML",
            reply_markup=create_main_menu_keyboard(),
        )
        return

    try:
        activation_info = await bot_service.check_user_activation(
            user_tag.replace("@", "")
        )

        if activation_info.get("has_activated_key"):
            status_text = (
                "📊 <b>Статус активации:</b>\n\n"
                "✅ <b>Ключ активирован</b>\n"
                f"🆔 ID ключа: {activation_info.get('key_id', 'N/A')}\n"
                f"📅 Активирован: {activation_info.get('created_at', 'N/A')}\n\n"
                "🎯 <b>Доступные действия:</b>\n"
                "/dialog - начать диалог\n"
                "/help - справка"
            )
        else:
            status_text = (
                "📊 <b>Статус активации:</b>\n\n"
                "❌ <b>Ключ не активирован</b>\n\n"
                "Используйте /activate &lt;ключ&gt; для активации"
            )

        await callback.message.edit_text(
            status_text, parse_mode="HTML", reply_markup=create_main_menu_keyboard()
        )

    except Exception as e:
        logger.error(f"Error getting status for user {user_id}: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка получения статуса</b>\n\nДетали: {str(e)}",
            parse_mode="HTML",
            reply_markup=create_main_menu_keyboard(),
        )


@commands_router.callback_query(F.data == "cmd_help")
async def callback_help(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Справка'."""
    current_state = await state.get_state()

    if current_state == ChatStates.waiting_for_activation:
        help_text = (
            "🆘 <b>Справка - Режим активации</b>\n\n"
            "🔑 <b>Для использования бота требуется активация ключа</b>\n\n"
            "📝 <b>Команды:</b>\n"
            "/start - перезапустить бота\n"
            "/activate &lt;ключ&gt; - активировать ключ\n"
            "/help - показать эту справку\n\n"
            "💡 <b>Как активировать:</b>\n"
            "1. Получите ключ у администратора\n"
            "2. Напишите /activate ABC123_DEF456\n"
            "3. Начните диалог командой /dialog"
        )
        keyboard = create_activation_menu_keyboard()
    elif current_state == ChatStates.activated:
        help_text = (
            "🆘 <b>Справка - Главное меню</b>\n\n"
            "✅ <b>Ваш ключ активирован</b>\n\n"
            "📝 <b>Команды:</b>\n"
            "/start - перезапустить бота\n"
            "/dialog - начать диалог\n"
            "/status - статус активации\n"
            "/help - показать эту справку\n\n"
            "💡 <b>Как пользоваться:</b>\n"
            "1. Нажмите 'Начать диалог'\n"
            "2. Задайте свой вопрос\n"
            "3. Получите ответ с источниками\n"
            "4. Выберите источник для просмотра выдержки"
        )
        keyboard = create_main_menu_keyboard()
    elif current_state == ChatStates.dialog_mode:
        help_text = (
            "🆘 <b>Справка - Режим диалога</b>\n\n"
            "🎯 <b>Вы в режиме диалога</b>\n\n"
            "📝 <b>Команды:</b>\n"
            "/end - завершить диалог\n"
            "/help - показать эту справку\n\n"
            "💡 <b>Как пользоваться:</b>\n"
            "1. Задайте вопрос в свободной форме\n"
            "2. Получите ответ на основе учебных материалов\n"
            "3. При наличии источников выберите номер (1-5) для просмотра выдержки\n"
            "4. Напишите 'выход' для завершения диалога\n\n"
            "⏰ <b>Важно:</b> Диалог завершится через 3 минуты бездействия"
        )
        keyboard = create_main_menu_keyboard()
    else:
        help_text = (
            "🆘 <b>Справка по командам:</b>\n\n"
            "📝 <b>Основные команды:</b>\n"
            "/start - запустить бота и проверить активацию\n"
            "/activate &lt;ключ&gt; - активировать ключ\n"
            "/dialog - начать диалог\n"
            "/status - статус активации\n"
            "/help - справка\n"
            "/history - история сообщений\n"
            "/end - завершить диалог\n\n"
            "💡 <b>Алгоритм работы:</b>\n"
            "1. /start - проверка активации\n"
            "2. /activate &lt;ключ&gt; - если не активирован\n"
            "3. /dialog - начало общения\n"
            "4. Вопрос → Ответ → Выбор источника"
        )
        keyboard = create_help_keyboard()

    await callback.message.edit_text(
        help_text, parse_mode="HTML", reply_markup=keyboard
    )


@commands_router.callback_query(F.data == "cmd_history")
async def callback_history(callback: CallbackQuery, bot_service: ChatBot) -> None:
    """Обработчик кнопки 'История'."""
    user_id = callback.from_user.id

    history = await bot_service.get_history(user_id)

    if not history:
        await callback.message.edit_text(
            "📝 История сообщений пуста.\n\nНачните диалог с помощью команды /dialog",
            reply_markup=create_main_menu_keyboard(),
        )
        return

    history_text = "📚 <b>История диалога:</b>\n\n"

    for i, entry in enumerate(history[-10:], 1):
        history_text += f"{i}. <b>Вы:</b> {entry['user_message'][:100]}{'...' if len(entry['user_message']) > 100 else ''}\n"
        history_text += f"   <b>Бот:</b> {entry['bot_response'][:100]}{'...' if len(entry['bot_response']) > 100 else ''}\n\n"

    if len(history) > 10:
        history_text += f"Показаны последние 10 из {len(history)} сообщений."

    await callback.message.edit_text(
        history_text, parse_mode="HTML", reply_markup=create_main_menu_keyboard()
    )

    logger.info(
        f"User {user_id} requested history via button ({len(history)} messages)"
    )


@commands_router.callback_query(F.data == "cmd_activate_info")
async def callback_activate_info(callback: CallbackQuery) -> None:
    """Обработчик кнопки 'Активировать ключ'."""
    await callback.message.edit_text(
        "🔑 <b>Активация ключа</b>\n\n"
        "Для активации ключа:\n"
        "1. Получите ключ у администратора\n"
        "2. Напишите: /activate [ваш_ключ]\n\n"
        "<i>Пример: /activate ABC123_DEF456</i>",
        parse_mode="HTML",
        reply_markup=create_activation_menu_keyboard(),
    )


@commands_router.callback_query(F.data == "cmd_start")
async def callback_start(
    callback: CallbackQuery, state: FSMContext, bot_service: ChatBot
) -> None:
    """Обработчик кнопки 'Главное меню'."""
    user_id = callback.from_user.id
    username = callback.from_user.username or f"user_{user_id}"
    user_tag = username

    activation_result = await bot_service.check_user_activation(user_tag)
    has_activated_key = (
        activation_result.get("has_activated_key", False)
        if isinstance(activation_result, dict)
        else activation_result
    )

    if has_activated_key:
        await state.set_state(ChatStates.activated)
        await state.update_data(user_tag=user_tag)

        welcome_text = (
            f"👋 Привет, {username}!\n\n"
            "✅ <b>У вас есть активированный ключ</b>\n\n"
            "🎯 <b>Выберите действие:</b>"
        )
        keyboard = create_main_menu_keyboard()
    else:
        await state.set_state(ChatStates.waiting_for_activation)

        welcome_text = (
            f"👋 Привет, {username}!\n\n"
            "🔑 <b>Для использования бота требуется активация ключа</b>\n\n"
            "<i>Получите ключ у администратора университета</i>"
        )
        keyboard = create_activation_menu_keyboard()

    await callback.message.edit_text(
        welcome_text, parse_mode="HTML", reply_markup=keyboard
    )


# Обработчик для всех остальных команд
@commands_router.message(F.text.startswith("/"))
async def cmd_unknown(message: Message) -> None:
    """Обработчик неизвестных команд."""
    await message.reply(
        f"❓ Неизвестная команда: {message.text}\n\n"
        "Используйте /help для списка доступных команд."
    )
