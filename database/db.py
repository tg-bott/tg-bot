import aiosqlite
import logging
from datetime import datetime, date

DB_PATH = "bot.db"
logger = logging.getLogger(__name__)


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                username    TEXT,
                first_name  TEXT,
                stage       TEXT NOT NULL,
                quantity    INTEGER NOT NULL,
                created_at  TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.commit()
        await _migrate_drop_unique_telegram_id(db)
    logger.info("Database initialized")


async def _migrate_drop_unique_telegram_id(db: aiosqlite.Connection) -> None:
    """Старые версии базы создавали bookings с UNIQUE(telegram_id), из-за чего
    у пользователя не могло быть больше одной брони — второе бронирование
    падало с ошибкой уникальности. 'CREATE TABLE IF NOT EXISTS' не меняет уже
    существующую таблицу, поэтому если такая база уже есть на диске,
    пересоздаём таблицу без этого ограничения, сохранив все записи."""
    async with db.execute("PRAGMA index_list(bookings)") as cur:
        indexes = await cur.fetchall()

    unique_on_telegram_id = False
    for idx in indexes:
        idx_name, is_unique = idx[1], idx[2]
        if not is_unique:
            continue
        async with db.execute(f"PRAGMA index_info({idx_name})") as cur2:
            cols = [row[2] for row in await cur2.fetchall()]
        if cols == ["telegram_id"]:
            unique_on_telegram_id = True
            break

    if not unique_on_telegram_id:
        return

    logger.info("Обнаружено устаревшее ограничение UNIQUE(telegram_id) — пересоздаю таблицу bookings")

    async with db.execute("PRAGMA table_info(bookings)") as cur:
        existing_cols = [row[1] for row in await cur.fetchall()]

    await db.execute("ALTER TABLE bookings RENAME TO bookings_old")
    await db.execute("""
        CREATE TABLE bookings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            username    TEXT,
            first_name  TEXT,
            stage       TEXT NOT NULL,
            quantity    INTEGER NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)

    common_cols = [c for c in
                   ("id", "telegram_id", "username", "first_name", "stage", "quantity", "created_at")
                   if c in existing_cols]
    cols_sql = ", ".join(common_cols)
    await db.execute(f"INSERT INTO bookings ({cols_sql}) SELECT {cols_sql} FROM bookings_old")
    await db.execute("DROP TABLE bookings_old")
    await db.commit()


async def get_user_bookings(telegram_id: int) -> list[dict]:
    """Все брони пользователя в порядке создания — используется для нумерации
    (раздел 'Мои заказы' и выбор конкретной брони для изменения/отмены)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM bookings WHERE telegram_id = ? ORDER BY id ASC",
            (telegram_id,)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_booking_by_id(booking_id: int) -> dict | None:
    """Возвращает конкретную бронь по её id (нужно для точечного управления записями)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM bookings WHERE id = ?",
            (booking_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def delete_booking_by_id(booking_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
        await db.commit()


async def create_booking(
    telegram_id: int, username: str | None, first_name: str,
    stage: str, quantity: int
) -> None:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO bookings
               (telegram_id, username, first_name, stage, quantity, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (telegram_id, username, first_name, stage, quantity, now),
        )
        await db.commit()


async def update_booking_by_id(
    booking_id: int, stage: str, quantity: int, username: str | None
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE bookings SET stage=?, quantity=?, username=? WHERE id=?",
            (stage, quantity, username, booking_id),
        )
        await db.commit()


async def get_today_stats() -> dict:
    today = date.today().strftime("%d.%m.%Y")
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*), COALESCE(SUM(quantity),0) FROM bookings WHERE created_at LIKE ?",
            (f"{today}%",),
        ) as cur:
            row = await cur.fetchone()
            return {"count": row[0], "total": row[1]}


async def get_all_bookings() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM bookings ORDER BY created_at DESC"
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_setting(key: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def set_setting(key: str, value: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await db.commit()