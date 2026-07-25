from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPPORT_LINKS, STAGES, ADMIN_IDS
from texts import BOOKING_OPTION_LABEL


def main_menu_kb(user_id: int = 0) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📦 Забронировать", callback_data="book")],
        [InlineKeyboardButton(text="💰 Узнать прайс",  callback_data="prices")],
        [InlineKeyboardButton(text="📋 Моя бронь",    callback_data="my_booking")],
        [InlineKeyboardButton(text="👨‍💻 Поддержка",   callback_data="support")],
    ]
    if user_id in ADMIN_IDS:
        buttons.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="open_admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def prices_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Забронировать", callback_data="book")],
        [InlineKeyboardButton(text="⬅️ Назад",         callback_data="back_main")],
    ])


def support_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=s["text"], url=f"https://t.me/{s['username']}")]
        for s in SUPPORT_LINKS
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def stages_kb(prefix: str = "stage") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=s, callback_data=f"{prefix}:{s}")]
        for s in STAGES
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    ])


def confirm_booking_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="✏️ Изменить",   callback_data="confirm_edit")],
        [InlineKeyboardButton(text="⬅️ Назад",      callback_data="back_main")],
    ])


def my_booking_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить бронь", callback_data="edit_booking")],
        [InlineKeyboardButton(text="❌ Отменить бронь", callback_data="cancel_booking")],
        [InlineKeyboardButton(text="⬅️ Назад",         callback_data="back_main")],
    ])


def bookings_select_kb(bookings: list[dict], action_prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора конкретной брони по номеру.
    action_prefix — например 'editpick' или 'cancelpick';
    callback_data получится вида '{action_prefix}:{booking_id}'."""
    buttons = []
    for index, b in enumerate(bookings, start=1):
        buttons.append([
            InlineKeyboardButton(
                text=BOOKING_OPTION_LABEL.format(index=index, stage=b["stage"], quantity=b["quantity"]),
                callback_data=f"{action_prefix}:{b['id']}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да",  callback_data="confirm_cancel_yes"),
            InlineKeyboardButton(text="Нет", callback_data="confirm_cancel_no"),
        ]
    ])