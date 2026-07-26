# Все тексты бота

WELCOME = (
    "Добро пожаловать в телефонию <b>ADMIN R</b>.\n\n"
    "Бронь сипов и круглосуточная поддержка саппортов: "
    "Бронируй свои сипы прямо сейчас!"
)

PRICES = (
    "1 этап — $120\n"
    "2 этап — $110\n"
    "3 этап — $110"
)

SUPPORT_HEADER = "Контакты актуальных саппортов:"

CHOOSE_STAGE = "Выберите этап:"

ENTER_QUANTITY = "Бронь <b>{stage}</b>\n\nУкажите количество сипов:"

ENTER_USERNAME = (
    "Укажите ваш Telegram username.\n\n"
    "Введите его в формате:\n\n"
    "@username"
)

# Показывается, если введённый username не прошёл проверку формата.
# Username обязателен — без него оформление брони продолжить нельзя.
INVALID_USERNAME = (
    "❌ Неверный формат username.\n\n"
    "Введите ваш Telegram username в формате:\n\n"
    "@username"
)

CONFIRM_TEXT = (
    "Проверьте данные:\n\n"
    "Этап:\n<b>{stage}</b>\n\n"
    "Количество:\n<b>{quantity}</b>\n\n"
    "Username:\n<b>{username}</b>"
)

BOOKING_SUCCESS = "✅ Ваша бронь успешно отправлена.\n\nОжидайте подтверждения."

ALREADY_HAS_BOOKING = "У вас уже есть активная бронь.\n\nВы можете изменить её."

NO_BOOKING = "У вас пока нет активной брони."

# Список броней пользователя (раздел "Мои заказы") — всегда с номерами,
# чтобы теми же номерами можно было выбрать бронь для изменения/отмены.
MY_BOOKINGS_HEADER = "<b>Ваши брони</b>\n\n"

MY_BOOKINGS_ROW = "<b>{index}.</b>\nЭтап: {stage}\nКоличество: {quantity}\n────────────\n"

# Короткая подпись брони для кнопок выбора
BOOKING_OPTION_LABEL = "{index}. {stage} — {quantity} шт."

CHOOSE_BOOKING_TO_EDIT = "У вас несколько броней.\n\nВыберите номер брони, которую хотите изменить:"

CHOOSE_BOOKING_TO_CANCEL = "У вас несколько броней.\n\nВыберите номер брони, которую хотите отменить:"

ENTER_NEW_QUANTITY = "Введите новое количество:"

QUANTITY_UPDATED = "✅ Количество успешно изменено."

CANCEL_CONFIRM = (
    "Вы действительно хотите отменить эту бронь?\n\n"
    "Этап: {stage}\nКоличество: {quantity}"
)

BOOKING_CANCELLED = "✅ Бронь отменена."

BOOKING_COMPLETED = "✅ Ваша бронь выполнена.\n\nСпасибо!"

NOT_A_NUMBER = "⚠️ Введите целое положительное число:"

# Уведомления администратору
ADMIN_NEW_BOOKING = (
    "📦 <b>Новая бронь</b>\n\n"
    "{username}\nЭтап: {stage}\nКол-во: {quantity}"
)

ADMIN_BOOKING_EDITED = (
    "✏️ <b>Бронь изменена</b>\n\n"
    "{username}\nЭтап: {stage}\nКол-во: {quantity}"
)

ADMIN_BOOKING_CANCELLED = (
    "❌ <b>Бронь отменена</b>\n\n"
    "{username}\nЭтап: {stage}\nКол-во: {quantity}"
)

ADMIN_TODAY = (
    "<b>Статистика на сегодня</b>\n\n"
    "Количество заявок:\n{count}\n\n"
    "Общее количество товара:\n{total}"
)

ADMIN_ALL_EMPTY = "Активных броней нет."

NOT_ADMIN = "⛔ Нет доступа."

          
