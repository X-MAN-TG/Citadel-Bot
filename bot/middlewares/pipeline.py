import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from aiogram import Bot
from aiogram.types import Update

from bot.utils.compat import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    CompatContext,
    CompatUpdate,
    MessageHandler,
    PreCheckoutQueryHandler,
    TypeHandler,
)

log = logging.getLogger(__name__)


async def handle_update(update: Update, bot: Bot, app: Any) -> None:
    # Check max update age (10 minutes)
    if update.message and update.message.date:
        msg_date = update.message.date
        now = datetime.now(timezone.utc)
        if msg_date.tzinfo is None:
            now = datetime.now()
        if now - msg_date > timedelta(minutes=10):
            return

    sorted_groups = sorted(app.handlers.keys())

    if update.message:
        msg = update.message
        for group in sorted_groups:
            for handler in app.handlers[group]:
                if isinstance(handler, CommandHandler):
                    matched, args = handler.matches(msg)
                    if matched:
                        c_upd = CompatUpdate(msg, bot, app.bot_data, app.job_queue)
                        c_ctx = CompatContext(bot, app.bot_data, app.job_queue, args=args, application=app)
                        try:
                            res = handler.callback(c_upd, c_ctx)
                            if asyncio.iscoroutine(res):
                                await res
                        except ApplicationHandlerStop:
                            return
                        except Exception as e:
                            c_ctx.error = e
                            for eh in app.error_handlers:
                                try:
                                    r = eh(c_upd, c_ctx)
                                    if asyncio.iscoroutine(r):
                                        await r
                                except Exception:
                                    log.exception("Error in error handler")
                        break
                elif isinstance(handler, MessageHandler):
                    if handler.matches(msg):
                        c_upd = CompatUpdate(msg, bot, app.bot_data, app.job_queue)
                        c_ctx = CompatContext(bot, app.bot_data, app.job_queue, args=[], application=app)
                        try:
                            res = handler.callback(c_upd, c_ctx)
                            if asyncio.iscoroutine(res):
                                await res
                        except ApplicationHandlerStop:
                            return
                        except Exception as e:
                            c_ctx.error = e
                            for eh in app.error_handlers:
                                try:
                                    r = eh(c_upd, c_ctx)
                                    if asyncio.iscoroutine(r):
                                        await r
                                except Exception:
                                    log.exception("Error in error handler")
                        break
                elif isinstance(handler, TypeHandler):
                    if isinstance(update, handler.type) or isinstance(msg, handler.type):
                        c_upd = CompatUpdate(msg, bot, app.bot_data, app.job_queue)
                        c_ctx = CompatContext(bot, app.bot_data, app.job_queue, args=[], application=app)
                        try:
                            res = handler.callback(c_upd, c_ctx)
                            if asyncio.iscoroutine(res):
                                await res
                        except ApplicationHandlerStop:
                            return
                        except Exception as e:
                            c_ctx.error = e
                            for eh in app.error_handlers:
                                try:
                                    r = eh(c_upd, c_ctx)
                                    if asyncio.iscoroutine(r):
                                        await r
                                except Exception:
                                    log.exception("Error in error handler")
                        break

    elif update.callback_query:
        cq = update.callback_query
        for group in sorted_groups:
            for handler in app.handlers[group]:
                if isinstance(handler, CallbackQueryHandler):
                    if handler.matches(cq):
                        c_upd = CompatUpdate(cq, bot, app.bot_data, app.job_queue)
                        c_ctx = CompatContext(bot, app.bot_data, app.job_queue, args=[], application=app)
                        try:
                            res = handler.callback(c_upd, c_ctx)
                            if asyncio.iscoroutine(res):
                                await res
                        except ApplicationHandlerStop:
                            return
                        except Exception as e:
                            c_ctx.error = e
                            for eh in app.error_handlers:
                                try:
                                    r = eh(c_upd, c_ctx)
                                    if asyncio.iscoroutine(r):
                                        await r
                                except Exception:
                                    log.exception("Error in error handler")
                        break

    elif update.my_chat_member:
        mcm = update.my_chat_member
        for group in sorted_groups:
            for handler in app.handlers[group]:
                if isinstance(handler, ChatMemberHandler):
                    c_upd = CompatUpdate(mcm, bot, app.bot_data, app.job_queue)
                    c_ctx = CompatContext(bot, app.bot_data, app.job_queue, args=[], application=app)
                    try:
                        res = handler.callback(c_upd, c_ctx)
                        if asyncio.iscoroutine(res):
                            await res
                    except ApplicationHandlerStop:
                        return
                    except Exception as e:
                        c_ctx.error = e
                        for eh in app.error_handlers:
                            try:
                                r = eh(c_upd, c_ctx)
                                if asyncio.iscoroutine(r):
                                    await r
                            except Exception:
                                log.exception("Error in error handler")
                    break

    elif update.pre_checkout_query:
        pcq = update.pre_checkout_query
        for group in sorted_groups:
            for handler in app.handlers[group]:
                if isinstance(handler, PreCheckoutQueryHandler):
                    c_upd = CompatUpdate(pcq, bot, app.bot_data, app.job_queue)
                    c_ctx = CompatContext(bot, app.bot_data, app.job_queue, args=[], application=app)
                    try:
                        res = handler.callback(c_upd, c_ctx)
                        if asyncio.iscoroutine(res):
                            await res
                    except ApplicationHandlerStop:
                        return
                    except Exception as e:
                        c_ctx.error = e
                        for eh in app.error_handlers:
                            try:
                                r = eh(c_upd, c_ctx)
                                if asyncio.iscoroutine(r):
                                    await r
                            except Exception:
                                log.exception("Error in error handler")
                    break
