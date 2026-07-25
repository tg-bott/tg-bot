# keyboards/admin.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import fmt_username


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Активные брони", callback_data="admin_bookings")],
        [InlineKeyboardButton(text="⬅️ Назад",          callback_data="back_main")],
    ])


def bookings_list_kb(bookings: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for b in bookings:
        # callback_data строится по id конкретной брони, а не по telegram_id —
        # у одного пользователя может быть несколько броней, и они не должны
        # получать одинаковый callback_data.
        booking_id = b["id"]
        # fmt_username гарантирует ровно один символ "@" независимо от того,
        # как username хранится в базе (с "@" или без).
        uname = fmt_username(b["username"]) if b["username"] else "без username"
        buttons.append([
            InlineKeyboardButton(
                text=f"✅ Выполнено — {uname} | {b['stage']} | {b['quantity']} шт",
                callback_data=f"done:{booking_id}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)