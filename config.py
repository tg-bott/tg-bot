import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Несколько админов: в .env укажи через запятую, например
# ADMIN_IDS=111111111,222222222,333333333
_raw_admin_ids = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID", "")
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in _raw_admin_ids.split(",") if x.strip().isdigit()
]

# Этапы — меняй здесь
STAGES: list[str] = ["1 этап", "2 этап", "3 этап"]

# Юзернеймы поддержки
SUPPORT_LINKS: list[dict] = [
    {"text": "Support 1", "username": "djuicesupport"},
    {"text": "Support 2", "username": "bubliksupp"},
    {"text": "Support 3", "username": "lexsuppik"},
]

# file_id фотографий — заполняется через команды /set_*_photo
# или вручную сюда (после того как отправишь фото боту и получишь file_id)
PHOTOS: dict[str, str] = {
    "main":    "",   # Меню
    "booking": "",   # Бронь сипов
    "my":      "",   # Ваша бронь
    "prices":  "",   # Прайс
    "support": "",   # Поддержка
}