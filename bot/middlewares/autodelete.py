"""Auto-delete the bot's replies to chosen commands in groups."""
import contextvars
from typing import Any

from aiogram.types import Message
from bot.utils.compat import CommandHandler

DELETE_AFTER_SECONDS = 15 * 60
DELETE_COMMANDS = {
    "wallet", "claim", "pay", "guard", "rob", "rankings",
    "vault", "deposit", "withdraw", "work", "spin", "mafiatop",
}

_active_jq = contextvars.ContextVar("autodel_jq", default=None)


async def _delete_job(context: Any) -> None:
    chat_id, message_id = context.job.data
    try:
        await context.bot.delete_message(chat_id, message_id)
    except Exception:
        pass  # already deleted or too old


def _patch_reply(name: str) -> None:
    orig = getattr(Message, name)

    async def inner(self: Message, *args: Any, **kwargs: Any) -> Any:
        sent = await orig(self, *args, **kwargs)
        jq = _active_jq.get()
        if jq is not None and getattr(self, "chat", None) and self.chat.type in ("group", "supergroup"):
            try:
                jq.run_once(
                    _delete_job,
                    DELETE_AFTER_SECONDS,
                    data=(sent.chat.id, sent.message_id),
                )
            except Exception:
                pass
        return sent

    setattr(Message, name, inner)


def _wrap(callback: Any, jq: Any) -> Any:
    async def wrapped(update: Any, context: Any) -> Any:
        token = _active_jq.set(jq)
        try:
            return await callback(update, context)
        finally:
            _active_jq.reset(token)

    return wrapped


def install(application: Any) -> None:
    for name in ("reply_text", "reply_html", "reply_photo"):
        _patch_reply(name)
    jq = application.job_queue
    count = 0
    for handlers in application.handlers.values():
        for h in handlers:
            if isinstance(h, CommandHandler) and (h.commands & DELETE_COMMANDS):
                h.callback = _wrap(h.callback, jq)
                count += 1
    print(f"Auto-delete active on {count} commands")
