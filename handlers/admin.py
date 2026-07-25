# admin.py
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS
from database.db import get_today_stats, get_all_bookings, set_setting, get_booking_by_id, delete_booking_by_id
from keyboards.admin import admin_menu_kb, bookings_list_kb
from texts import ADMIN_TODAY, ADMIN_ALL_EMPTY, NOT_ADMIN, BOOKING_COMPLETED
from utils.helpers import fmt_username

router = Router()
logger = logging.getLogger(__name__)


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


async def safe_answer(callback: CallbackQuery) -> None:
    """Протухший (слишком старый) callback не должен ронять обработчик трейсбеком."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass


async def safe_edit(callback: CallbackQuery, text: str, kb: InlineKeyboardMarkup) -> None:
    """Редактирует текущее сообщение админ-панели независимо от того, фото оно
    сейчас или обычный текст. Раньше в разных хендлерах был только edit_text,
    из-за чего кнопки молча переставали работать, если сообщение оказывалось
    фото (например, после открытия панели поверх фото главного меню)."""
    msg = callback.message
    if msg.photo:
        try:
            await msg.edit_caption(caption=text, reply_markup=kb, parse_mode="HTML")
            return
        except TelegramBadRequest:
            pass
    try:
        await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
        return
    except TelegramBadRequest:
        pass
    # Крайний случай — не смогли отредактировать ни как фото, ни как текст
    await msg.answer(text, reply_markup=kb, parse_mode="HTML")


def build_bookings_text(bookings: list[dict]) -> str:
    """Формирует текст со списком активных броней для админ-панели."""
    if not bookings:
        return ADMIN_ALL_EMPTY

    lines = ["<b>📋 Активные брони</b>\n"]
    for b in bookings:
        # fmt_username гарантирует ровно один символ "@" независимо от того,
        # как username хранится в базе (с "@" или без).
        uname = fmt_username(b["username"]) if b["username"] else "Username отсутствует"
        lines.append(f"{uname}\nЭтап: {b['stage']}\nКоличество: {b['quantity']}\n")
    return "\n".join(lines)


async def _bookings_view() -> tuple[str, InlineKeyboardMarkup]:
    """Общая логика получения текста + клавиатуры списка броней (убирает дублирование)."""
    bookings = await get_all_bookings()
    return build_bookings_text(bookings), bookings_list_kb(bookings)


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer(NOT_ADMIN)
        return
    await message.answer(
        "👨‍💼 <b>Панель администратора</b>",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_close")
async def admin_close(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        return
    await safe_answer(callback)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass


# ── Активные брони ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_bookings")
async def admin_bookings(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        return
    await safe_answer(callback)
    text, kb = await _bookings_view()
    await safe_edit(callback, text, kb)


@router.callback_query(F.data.startswith("done:"))
async def mark_done(callback: CallbackQuery, bot: Bot) -> None:
    if not is_admin(callback.from_user.id):
        return
    await safe_answer(callback)

    booking_id = int(callback.data.split(":")[1])
    booking = await get_booking_by_id(booking_id)

    if booking:
        # Удаляем только выбранную запись, а не последнюю бронь пользователя
        await delete_booking_by_id(booking_id)
        try:
            await bot.send_message(booking["telegram_id"], BOOKING_COMPLETED, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {booking['telegram_id']}: {e}")

    # Обновляем список
    text, kb = await _bookings_view()
    await safe_edit(callback, text, kb)


@router.callback_query(F.data == "open_admin")
async def open_admin(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        return
    await safe_answer(callback)
    await safe_edit(callback, "👨‍💼 <b>Панель администратора</b>", admin_menu_kb())

# ── /today и /all (текстовые команды) ────────────────────────────────────────

@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer(NOT_ADMIN)
        return
    stats = await get_today_stats()
    await message.answer(
        ADMIN_TODAY.format(count=stats["count"], total=stats["total"]),
        parse_mode="HTML",
    )


@router.message(Command("bookings", "all"))
async def cmd_bookings(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer(NOT_ADMIN)
        return
    text, kb = await _bookings_view()
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ── Смена фото разделов ───────────────────────────────────────────────────────

@router.message(F.photo & F.caption.func(lambda c: c and c.startswith("/set_")))
async def set_section_photo(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    caption = message.caption or ""
    mapping = {
        "/set_main_photo":    "main",
        "/set_booking_photo": "booking",
        "/set_my_photo":      "my",
        "/set_prices_photo":  "prices",
        "/set_support_photo": "support",
    }
    for cmd, key in mapping.items():
        if caption.startswith(cmd):
            file_id = message.photo[-1].file_id
            await set_setting(f"photo_{key}", file_id)
            await message.answer(f"✅ Фото «{key}» обновлено.")
            return
    await message.answer("Неизвестная команда.")


@router.message(Command("help_admin"))
async def cmd_help_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "<b>Команды администратора:</b>\n\n"
        "/admin — панель управления\n"
        "/bookings — брони с кнопками выполнения\n"
        "/today — статистика за сегодня\n\n"
        "<b>Смена фото</b> (отправь фото с подписью):\n"
        "<code>/set_main_photo</code>\n"
        "<code>/set_booking_photo</code>\n"
        "<code>/set_my_photo</code>\n"
        "<code>/set_prices_photo</code>\n"
        "<code>/set_support_photo</code>",
        parse_mode="HTML",
    )