import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS
from database.db import (
    get_user_bookings, get_booking_by_id, create_booking,
    update_booking_by_id, delete_booking_by_id,
)
from keyboards.main import (
    stages_kb, back_main_kb, my_booking_kb, confirm_booking_kb,
    confirm_cancel_kb, bookings_select_kb,
)
from states.booking import BookingFSM
from texts import (
    CHOOSE_STAGE, ENTER_QUANTITY, ENTER_USERNAME, CONFIRM_TEXT,
    BOOKING_SUCCESS, NO_BOOKING, MY_BOOKINGS_HEADER, MY_BOOKINGS_ROW,
    CHOOSE_BOOKING_TO_EDIT, CHOOSE_BOOKING_TO_CANCEL,
    CANCEL_CONFIRM, BOOKING_CANCELLED, NOT_A_NUMBER,
    ADMIN_NEW_BOOKING, ADMIN_BOOKING_EDITED, ADMIN_BOOKING_CANCELLED,
)
from utils.helpers import send_main_menu, edit_to_section, safe_delete, fmt_username

router = Router()
logger = logging.getLogger(__name__)


async def notify_admin(bot: Bot, text: str) -> None:
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось уведомить админа {admin_id}: {e}")


async def try_edit(bot: Bot, chat_id: int, msg_id: int, text: str, kb) -> bool:
    for method in (
        lambda: bot.edit_message_caption(
            chat_id=chat_id, message_id=msg_id,
            caption=text, reply_markup=kb, parse_mode="HTML"
        ),
        lambda: bot.edit_message_text(
            text=text, chat_id=chat_id, message_id=msg_id,
            reply_markup=kb, parse_mode="HTML"
        ),
    ):
        try:
            await method()
            return True
        except TelegramBadRequest:
            continue
    return False


async def show_confirm(bot: Bot, chat_id: int, state: FSMContext,
                       stage: str, quantity: int, username) -> None:
    display = fmt_username(username)
    text = CONFIRM_TEXT.format(stage=stage, quantity=quantity, username=display)
    kb = confirm_booking_kb()
    data = await state.get_data()
    bot_msg_id = data.get("bot_msg_id")

    if bot_msg_id:
        ok = await try_edit(bot, chat_id, bot_msg_id, text, kb)
        if ok:
            return

    sent = await bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
    await state.update_data(bot_msg_id=sent.message_id)


def build_my_bookings_text(user_bookings: list[dict]) -> str:
    """Нумерованный список броней пользователя — теми же номерами затем
    можно выбрать конкретную бронь для изменения/отмены."""
    text = MY_BOOKINGS_HEADER
    for index, b in enumerate(user_bookings, start=1):
        text += MY_BOOKINGS_ROW.format(index=index, stage=b["stage"], quantity=b["quantity"])
    return text


# ── Бронирование ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "book")
async def start_booking(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await state.set_state(BookingFSM.choosing_stage)
    await state.update_data(bot_msg_id=callback.message.message_id)
    await edit_to_section(callback, "booking", CHOOSE_STAGE, stages_kb("stage"))


@router.callback_query(BookingFSM.choosing_stage, F.data.startswith("stage:"))
async def stage_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    stage = callback.data.split(":", 1)[1]
    await state.update_data(stage=stage, bot_msg_id=callback.message.message_id)
    await state.set_state(BookingFSM.entering_quantity)
    await edit_to_section(callback, "booking", ENTER_QUANTITY.format(stage=stage), back_main_kb())


@router.message(BookingFSM.entering_quantity)
async def enter_quantity(message: Message, state: FSMContext, bot: Bot) -> None:
    chat_id = message.chat.id
    text = (message.text or "").strip()
    await safe_delete(bot, chat_id, message.message_id)

    data = await state.get_data()
    bot_msg_id = data.get("bot_msg_id")
    stage = data.get("stage", "")

    if not text.isdigit() or int(text) <= 0:
        if bot_msg_id:
            await try_edit(bot, chat_id, bot_msg_id,
                           f"{ENTER_QUANTITY.format(stage=stage)}\n\n{NOT_A_NUMBER}",
                           back_main_kb())
        return

    await state.update_data(quantity=int(text))
    await state.set_state(BookingFSM.entering_username)

    if bot_msg_id:
        ok = await try_edit(bot, chat_id, bot_msg_id, ENTER_USERNAME, back_main_kb())
        if not ok:
            sent = await bot.send_message(chat_id, ENTER_USERNAME,
                                          reply_markup=back_main_kb(), parse_mode="HTML")
            await state.update_data(bot_msg_id=sent.message_id)
    else:
        sent = await bot.send_message(chat_id, ENTER_USERNAME,
                                      reply_markup=back_main_kb(), parse_mode="HTML")
        await state.update_data(bot_msg_id=sent.message_id)


@router.message(BookingFSM.entering_username)
async def enter_username(message: Message, state: FSMContext, bot: Bot) -> None:
    chat_id = message.chat.id
    raw = (message.text or "").strip()
    await safe_delete(bot, chat_id, message.message_id)

    username = None if raw in ("—", "-", "") else raw.lstrip("@")
    data = await state.get_data()

    await state.update_data(username=username)
    await state.set_state(BookingFSM.confirming)

    await show_confirm(bot, chat_id, state, data["stage"], data["quantity"], username)


@router.callback_query(BookingFSM.confirming, F.data == "confirm_yes")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer()
    data = await state.get_data()
    stage = data["stage"]
    quantity = data["quantity"]
    username = data.get("username")
    user = callback.from_user

    await create_booking(user.id, username, user.first_name or "—", stage, quantity)
    await state.clear()

    await edit_to_section(callback, "main", BOOKING_SUCCESS, back_main_kb())
    await notify_admin(bot, ADMIN_NEW_BOOKING.format(
        username=fmt_username(username), stage=stage, quantity=quantity
    ))


@router.callback_query(BookingFSM.confirming, F.data == "confirm_edit")
async def confirm_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(bot_msg_id=callback.message.message_id)
    await state.set_state(BookingFSM.choosing_stage)
    await edit_to_section(callback, "booking", CHOOSE_STAGE, stages_kb("stage"))


# ── Моя бронь ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "my_booking")
async def my_booking(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    user_bookings = await get_user_bookings(callback.from_user.id)

    if not user_bookings:
        await edit_to_section(callback, "my", NO_BOOKING, back_main_kb())
        return

    text = build_my_bookings_text(user_bookings)
    await edit_to_section(callback, "my", text, my_booking_kb())


# ── Изменение брони ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "edit_booking")
async def edit_booking_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()

    user_bookings = await get_user_bookings(callback.from_user.id)

    if not user_bookings:
        await edit_to_section(callback, "my", NO_BOOKING, back_main_kb())
        return

    if len(user_bookings) == 1:
        await state.update_data(edit_booking_id=user_bookings[0]["id"],
                                 bot_msg_id=callback.message.message_id)
        await state.set_state(BookingFSM.editing_stage)
        await edit_to_section(callback, "booking", CHOOSE_STAGE, stages_kb("editstage"))
        return

    await state.set_state(BookingFSM.choosing_edit_target)
    await edit_to_section(callback, "my", CHOOSE_BOOKING_TO_EDIT,
                          bookings_select_kb(user_bookings, "editpick"))


@router.callback_query(BookingFSM.choosing_edit_target, F.data.startswith("editpick:"))
async def edit_target_picked(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    booking_id = int(callback.data.split(":", 1)[1])
    await state.update_data(edit_booking_id=booking_id, bot_msg_id=callback.message.message_id)
    await state.set_state(BookingFSM.editing_stage)
    await edit_to_section(callback, "booking", CHOOSE_STAGE, stages_kb("editstage"))


@router.callback_query(BookingFSM.editing_stage, F.data.startswith("editstage:"))
async def edit_stage_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    stage = callback.data.split(":", 1)[1]
    await state.update_data(stage=stage, bot_msg_id=callback.message.message_id)
    await state.set_state(BookingFSM.editing_quantity)
    await edit_to_section(callback, "booking", ENTER_QUANTITY.format(stage=stage), back_main_kb())


@router.message(BookingFSM.editing_quantity)
async def edit_quantity(message: Message, state: FSMContext, bot: Bot) -> None:
    chat_id = message.chat.id
    text = (message.text or "").strip()
    await safe_delete(bot, chat_id, message.message_id)

    data = await state.get_data()
    bot_msg_id = data.get("bot_msg_id")
    stage = data.get("stage", "")

    if not text.isdigit() or int(text) <= 0:
        if bot_msg_id:
            await try_edit(bot, chat_id, bot_msg_id,
                           f"{ENTER_QUANTITY.format(stage=stage)}\n\n{NOT_A_NUMBER}",
                           back_main_kb())
        return

    await state.update_data(quantity=int(text))
    await state.set_state(BookingFSM.editing_username)

    if bot_msg_id:
        ok = await try_edit(bot, chat_id, bot_msg_id, ENTER_USERNAME, back_main_kb())
        if not ok:
            sent = await bot.send_message(chat_id, ENTER_USERNAME,
                                          reply_markup=back_main_kb(), parse_mode="HTML")
            await state.update_data(bot_msg_id=sent.message_id)
    else:
        sent = await bot.send_message(chat_id, ENTER_USERNAME,
                                      reply_markup=back_main_kb(), parse_mode="HTML")
        await state.update_data(bot_msg_id=sent.message_id)


@router.message(BookingFSM.editing_username)
async def edit_username(message: Message, state: FSMContext, bot: Bot) -> None:
    chat_id = message.chat.id
    raw = (message.text or "").strip()
    await safe_delete(bot, chat_id, message.message_id)

    username = None if raw in ("—", "-", "") else raw.lstrip("@")
    data = await state.get_data()

    await state.update_data(username=username)
    await state.set_state(BookingFSM.editing_confirm)

    await show_confirm(bot, chat_id, state, data["stage"], data["quantity"], username)


@router.callback_query(BookingFSM.editing_confirm, F.data == "confirm_yes")
async def edit_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer()
    data = await state.get_data()
    booking_id = data["edit_booking_id"]
    stage = data["stage"]
    quantity = data["quantity"]
    username = data.get("username")

    await update_booking_by_id(booking_id, stage, quantity, username)
    await state.clear()

    await edit_to_section(callback, "main", "✅ Бронь обновлена.", back_main_kb())
    await notify_admin(bot, ADMIN_BOOKING_EDITED.format(
        username=fmt_username(username), stage=stage, quantity=quantity
    ))


@router.callback_query(BookingFSM.editing_confirm, F.data == "confirm_edit")
async def edit_again(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(bot_msg_id=callback.message.message_id)
    await state.set_state(BookingFSM.editing_stage)
    await edit_to_section(callback, "booking", CHOOSE_STAGE, stages_kb("editstage"))


# ── Отмена брони ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel_booking")
async def cancel_booking_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    user_bookings = await get_user_bookings(callback.from_user.id)

    if not user_bookings:
        await edit_to_section(callback, "my", NO_BOOKING, back_main_kb())
        return

    if len(user_bookings) == 1:
        booking = user_bookings[0]
        await state.update_data(cancel_booking_id=booking["id"])
        await state.set_state(BookingFSM.confirming_cancel)
        await edit_to_section(
            callback, "my",
            CANCEL_CONFIRM.format(stage=booking["stage"], quantity=booking["quantity"]),
            confirm_cancel_kb(),
        )
        return

    await state.set_state(BookingFSM.choosing_cancel_target)
    await edit_to_section(callback, "my", CHOOSE_BOOKING_TO_CANCEL,
                          bookings_select_kb(user_bookings, "cancelpick"))


@router.callback_query(BookingFSM.choosing_cancel_target, F.data.startswith("cancelpick:"))
async def cancel_target_picked(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    booking_id = int(callback.data.split(":", 1)[1])
    booking = await get_booking_by_id(booking_id)

    if not booking:
        await send_main_menu(callback, state)
        return

    await state.update_data(cancel_booking_id=booking_id)
    await state.set_state(BookingFSM.confirming_cancel)
    await edit_to_section(
        callback, "my",
        CANCEL_CONFIRM.format(stage=booking["stage"], quantity=booking["quantity"]),
        confirm_cancel_kb(),
    )


@router.callback_query(BookingFSM.confirming_cancel, F.data == "confirm_cancel_yes")
async def cancel_yes(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    await callback.answer()
    data = await state.get_data()
    booking_id = data.get("cancel_booking_id")
    booking = await get_booking_by_id(booking_id) if booking_id else None

    if not booking:
        await state.clear()
        await send_main_menu(callback, state)
        return

    await delete_booking_by_id(booking_id)
    await state.clear()

    await edit_to_section(callback, "main", BOOKING_CANCELLED, back_main_kb())
    await notify_admin(bot, ADMIN_BOOKING_CANCELLED.format(
        username=fmt_username(booking.get("username")),
        stage=booking["stage"],
        quantity=booking["quantity"],
    ))


@router.callback_query(BookingFSM.confirming_cancel, F.data == "confirm_cancel_no")
async def cancel_no(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()

    user_bookings = await get_user_bookings(callback.from_user.id)

    if not user_bookings:
        await send_main_menu(callback, state)
        return

    text = build_my_bookings_text(user_bookings)
    await edit_to_section(callback, "my", text, my_booking_kb())