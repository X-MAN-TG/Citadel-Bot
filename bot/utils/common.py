"""Shared helpers for the Astraea-style features in Saloni."""
import html
import time as _time
from types import SimpleNamespace
from typing import Any, Optional

from bot.utils.compat import InlineKeyboardButton

ADMIN_STATES = ("administrator", "creator")

ANON_ON = set()
_ADMIN_CACHE = {}


def esc(text: Any) -> str:
    return html.escape(str(text))


def btn(text: str, data: Optional[str] = None, url: Optional[str] = None, style: Optional[str] = None) -> InlineKeyboardButton:
    """style: 'success' green, 'danger' red, 'primary' blue, None normal."""
    kw = {"style": style} if style else {}
    if url:
        return InlineKeyboardButton(text=text, url=url, **kw)
    return InlineKeyboardButton(text=text, callback_data=data, **kw)


async def is_admin(bot: Any, chat_id: int, user_id: int) -> bool:
    if user_id == 1087968824:
        return chat_id in ANON_ON
    now = _time.time()
    hit = _ADMIN_CACHE.get((chat_id, user_id))
    if hit and now - hit[1] < 15:
        return hit[0]
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        ok = m.status in ADMIN_STATES
    except Exception:
        return False
    _ADMIN_CACHE[(chat_id, user_id)] = (ok, now)
    return ok


async def bot_is_admin(bot: Any, chat_id: int) -> bool:
    return await is_admin(bot, chat_id, bot.id)


async def find_user_by_username(pool: Any, username: str) -> Optional[Any]:
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT id, first_name FROM users WHERE username ILIKE $1", username
        )


async def resolve_target(update: Any, context: Any, pool: Any) -> Optional[Any]:
    """Reply, tap-mention, numeric id or @username. Returns an object
    with .id and .first_name, or None."""
    msg = update.effective_message
    if msg and msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user
    for ent in (msg.entities or []) if msg else []:
        if getattr(ent, "type", None) == "text_mention" and getattr(ent, "user", None):
            return ent.user
    args = context.args or []
    if not args:
        return None
    ident = args[0]
    if ident.lstrip("-").isdigit():
        try:
            m = await context.bot.get_chat_member(update.effective_chat.id, int(ident))
            return m.user
        except Exception:
            return None
    row = await find_user_by_username(pool, ident.lstrip("@"))
    if row:
        return SimpleNamespace(id=row["id"], first_name=row["first_name"] or "User")
    return None


async def track_user(pool: Any, user: Any, chat: Any) -> None:
    """Remember users and group members; never creates wallets."""
    if user is None or getattr(user, "is_bot", False):
        return
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (id, username, first_name) VALUES ($1, $2, $3) "
            "ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username, "
            "first_name = EXCLUDED.first_name, updated_at = now()",
            user.id, user.username, user.first_name,
        )
        await conn.execute(
            "INSERT INTO ax_user_stats (user_id, message_count) VALUES ($1, 1) "
            "ON CONFLICT (user_id) DO UPDATE SET last_seen = now(), "
            "message_count = ax_user_stats.message_count + 1",
            user.id,
        )
        if chat is not None and getattr(chat, "type", None) != "private":
            await conn.execute(
                "INSERT INTO ax_chat_members (chat_id, user_id) VALUES ($1, $2) "
                "ON CONFLICT DO NOTHING",
                chat.id, user.id,
            )
