import sys
import types
from typing import Any

from aiogram.enums import ChatType, ParseMode, MessageEntityType
from bot.utils.compat import (
    ApplicationHandlerStop,
    BadRequest,
    CallbackQueryHandler,
    ChatMemberHandler,
    ChatMemberStatus,
    ChatPermissions,
    CommandHandler,
    Forbidden,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    InputSticker,
    MessageHandler,
    NetworkError,
    PreCheckoutQueryHandler,
    RetryAfter,
    TelegramError,
    TimedOut,
    TypeHandler,
    filters,
)
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    Document,
    File,
    Message,
    MessageEntity,
    PreCheckoutQuery,
    Update,
    User,
)


def install_shims() -> None:
    # 1. telegram
    tg = types.ModuleType("telegram")
    tg.InlineKeyboardButton = InlineKeyboardButton
    tg.InlineKeyboardMarkup = InlineKeyboardMarkup
    tg.InputFile = InputFile
    tg.InputSticker = InputSticker
    tg.ChatPermissions = ChatPermissions
    tg.Update = Update
    tg.Message = Message
    tg.CallbackQuery = CallbackQuery
    tg.ChatMemberUpdated = ChatMemberUpdated
    tg.PreCheckoutQuery = PreCheckoutQuery
    tg.User = User
    tg.Document = Document
    tg.File = File
    tg.MessageEntity = MessageEntity
    from aiogram.types import LinkPreviewOptions
    tg.LinkPreviewOptions = LinkPreviewOptions
    sys.modules["telegram"] = tg

    # 2. telegram.constants
    tg_const = types.ModuleType("telegram.constants")
    tg_const.ParseMode = ParseMode
    tg_const.ChatMemberStatus = ChatMemberStatus
    tg_const.ChatType = ChatType
    tg_const.MessageEntityType = MessageEntityType
    sys.modules["telegram.constants"] = tg_const
    tg.constants = tg_const

    # 3. telegram.error
    tg_err = types.ModuleType("telegram.error")
    tg_err.TelegramError = TelegramError
    tg_err.BadRequest = BadRequest
    tg_err.Forbidden = Forbidden
    tg_err.RetryAfter = RetryAfter
    tg_err.NetworkError = NetworkError
    tg_err.TimedOut = TimedOut
    tg_err.Conflict = TelegramError
    sys.modules["telegram.error"] = tg_err
    tg.error = tg_err

    # 4. telegram.ext
    tg_ext = types.ModuleType("telegram.ext")
    tg_ext.Application = Any
    tg_ext.ApplicationHandlerStop = ApplicationHandlerStop
    tg_ext.CommandHandler = CommandHandler
    tg_ext.CallbackQueryHandler = CallbackQueryHandler
    tg_ext.MessageHandler = MessageHandler
    tg_ext.ChatMemberHandler = ChatMemberHandler
    tg_ext.PreCheckoutQueryHandler = PreCheckoutQueryHandler
    tg_ext.TypeHandler = TypeHandler
    tg_ext.filters = filters

    class _ContextTypes:
        DEFAULT_TYPE = Any

    tg_ext.ContextTypes = _ContextTypes
    sys.modules["telegram.ext"] = tg_ext
    tg.ext = tg_ext


install_shims()
