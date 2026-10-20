import logging
import time
from typing import Any

from aiogram.types import Update
from bot.utils.compat import BadRequest, NetworkError, RetryAfter

log = logging.getLogger(__name__)
_last_notice = {}
_QUIET = (
    "message is not modified",
    "message to be replied not found",
    "message to edit not found",
    "query is too old",
)


def _wants_notice(update: Any) -> bool:
    if getattr(update, "callback_query", None):
        return True
    m = getattr(update, "effective_message", None)
    t = (m.text or m.caption or "") if m else ""
    return t.startswith("/")


async def on_error(update: Any, context: Any) -> None:
    err = context.error
    if isinstance(err, (NetworkError, RetryAfter)):
        log.warning("telegram transient error: %s", err)
        return
    if isinstance(err, BadRequest) and any(p in str(err).lower() for p in _QUIET):
        log.warning("harmless bad request: %s", err)
        return
    log.error("Unhandled error", exc_info=err)
    if (
        isinstance(update, Update) or hasattr(update, "effective_chat")
    ) and getattr(update, "effective_chat", None) and getattr(update, "effective_message", None) and _wants_notice(update):
        cid = update.effective_chat.id
        now = time.time()
        if now - _last_notice.get(cid, 0) < 30:
            return
        _last_notice[cid] = now
        try:
            await update.effective_message.reply_text(
                "⚠️ <b>Something went wrong</b>\n"
                "<blockquote>I noted it. Please try again in a moment 💫</blockquote>",
                parse_mode="HTML",
            )
        except Exception:
            log.warning("could not send error notice")


handle_error = on_error


def register(application: Any) -> None:
    application.add_error_handler(on_error)
