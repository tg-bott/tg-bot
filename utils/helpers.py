# helpers.py
import logging
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from config import PHOTOS
from database.db import get_setting
from keyboards.main import main_menu_kb
from texts import WELCOME
import re

logger = logging.getLogger(__name__)

USERNAME_RE = re.compile(r"^@[A-Za-z0-9_]{4,31}$")


def is_valid_username(text: str | None) -> bool:
    if not text:
        return False
    return bool(USERNAME_RE.match(text.strip()))


async def get_photo(key: str) -> str | None:
    from_db = await get_setting(f"photo_{key}")
    if from_db:
        return from_db
    return PHOTOS.get(key) or None


async def _send_new_main_message(
    bot: Bot,
    chat_id: int,
    user_id: int,
    photo_id: str | None,
    state: FSMContext,
) -> None:
    """Отправляет новое главное сообщение и сохраняет его id в FSM-хранилище.
    Используется как единая точка отправки — чтобы пользователь никогда
    не оставался без ответа, если старое сообщение отредактировать нельзя
    (удалено, история очищена и т.п.)."""
    try:
        if photo_id:
            msg = await bot.send_photo(
                chat_id, photo_id, caption=WELCOME,
                reply_markup=main_menu_kb(user_id=user_id), parse_mode="HTML",
            )
        else:
            msg = await bot.send_message(
                chat_id, WELCOME,
                reply_markup=main_menu_kb(user_id=user_id), parse_mode="HTML",
            )
        await state.update_data(main_message_id=msg.message_id, main_chat_id=chat_id)
    except Exception:
        logger.exception("Не удалось отправить главное меню пользователю %s", user_id)


async def send_main_menu(target: Message | CallbackQuery, state: FSMContext) -> None:
    """Отправляет или редактирует главное меню. Всегда сбрасывает FSM
    (кроме служебных полей main_message_id/main_chat_id, которые нужны для
    последующего редактирования)."""
    await state.clear()
    photo_id = await get_photo("main")

    if isinstance(target, CallbackQuery):
        msg = target.message
        user_id = target.from_user.id if hasattr(target, "from_user") else 0
        chat_id = msg.chat.id

        edited = False
        try:
            if photo_id:
                await msg.edit_media(
                    InputMediaPhoto(media=photo_id, caption=WELCOME, parse_mode="HTML"),
                    reply_markup=main_menu_kb(user_id=user_id),
                )
            else:
                await msg.edit_text(
                    WELCOME,
                    reply_markup=main_menu_kb(user_id=user_id),
                    parse_mode="HTML",
                )
            edited = True
        except TelegramBadRequest as e:
            # Сообщение могло быть удалено (например, история очищена),
            # либо тип контента не совпадает (фото/текст) — в любом случае
            # не роняем обработчик, а отправим новое сообщение ниже.
            logger.warning("Не удалось отредактировать главное меню: %s", e)
        except Exception:
            # Любая другая ошибка редактирования тоже не должна оставлять
            # пользователя без ответа.
            logger.exception("Неожиданная ошибка при редактировании главного меню")

        if edited:
            await state.update_data(main_message_id=msg.message_id, main_chat_id=chat_id)
        else:
            await _send_new_main_message(target.bot, chat_id, user_id, photo_id, state)
    else:
        user_id = target.from_user.id if hasattr(target, "from_user") else 0
        await _send_new_main_message(target.bot, target.chat.id, user_id, photo_id, state)


async def edit_to_section(
    callback: CallbackQuery,
    photo_key: str,
    text: str,
    keyboard,
) -> None:
    """Редактирует текущее сообщение под нужный раздел. Если редактирование
    невозможно (сообщение удалено и т.п.) — отправляет новое сообщение,
    чтобы пользователь не остался без ответа."""
    photo_id = await get_photo(photo_key)
    msg = callback.message

    async def send_new() -> None:
        try:
            if photo_id:
                await msg.answer_photo(photo_id, caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await msg.answer(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            logger.exception("Не удалось отправить новое сообщение раздела '%s'", photo_key)

    try:
        if photo_id:
            await msg.edit_media(
                InputMediaPhoto(media=photo_id, caption=text, parse_mode="HTML"),
                reply_markup=keyboard,
            )
        else:
            try:
                await msg.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
            except TelegramBadRequest:
                await msg.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except TelegramBadRequest as e:
        logger.warning("Не удалось отредактировать сообщение раздела '%s': %s", photo_key, e)
        await send_new()
    except Exception:
        logger.exception("Неожиданная ошибка при редактировании раздела '%s'", photo_key)
        await send_new()


async def safe_delete(bot: Bot, chat_id: int, message_id: int) -> None:
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass


def fmt_username(username: str | None) -> str:
    if not username:
        return "отсутствует"
    u = username.lstrip("@")
    return f"@{u}" if u else "отсутствует"