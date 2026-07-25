# menu.py
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from keyboards.main import prices_kb, support_kb
from texts import PRICES, SUPPORT_HEADER
from utils.helpers import send_main_menu, edit_to_section

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    try:
        await send_main_menu(message, state)
    except Exception:
        # На случай непредвиденной ошибки при отправке главного меню —
        # пользователь всё равно не должен остаться без ответа.
        logger.exception("Ошибка при обработке /start для пользователя %s", message.from_user.id)
        try:
            await message.answer("⚠️ Произошла ошибка, попробуйте ещё раз: /start")
        except Exception:
            pass


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

    try:
        await send_main_menu(callback, state)
    except Exception:
        logger.exception("Ошибка при обработке кнопки 'Старт' для пользователя %s", callback.from_user.id)
        try:
            await callback.message.answer("⚠️ Произошла ошибка, попробуйте ещё раз: /start")
        except Exception:
            pass


@router.callback_query(F.data == "prices")
async def show_prices(callback: CallbackQuery) -> None:
    await callback.answer()
    await edit_to_section(callback, "prices", PRICES, prices_kb())


@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery) -> None:
    await callback.answer()
    await edit_to_section(callback, "support", SUPPORT_HEADER, support_kb())