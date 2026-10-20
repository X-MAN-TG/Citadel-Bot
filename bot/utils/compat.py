import asyncio
import io
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from aiogram import Bot, Router
from aiogram.enums import ChatAction, ChatType, MessageEntityType, ParseMode
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    ChatMemberUpdated,
    ChatPermissions,
    Document,
    File,
    FSInputFile,
    InlineKeyboardButton as _AiogramIKB,
    InlineKeyboardMarkup as _AiogramIKM,
    InputSticker as _AiogramInputSticker,
    LabeledPrice,
    LinkPreviewOptions,
    Message,
    MessageEntity,
    PreCheckoutQuery,
    Update,
)

# Exception aliases
TelegramError = TelegramAPIError
BadRequest = TelegramBadRequest
Forbidden = TelegramForbiddenError
RetryAfter = TelegramRetryAfter
NetworkError = TelegramNetworkError
TimedOut = TelegramNetworkError


class _ContextDefault:
    pass


class ContextTypes:
    DEFAULT = _ContextDefault
    DEFAULT_TYPE = Any


Application = Any


class ApplicationHandlerStop(Exception):
    """Raised to immediately halt handler execution for the current update."""
    pass


class ChatMemberStatus:
    CREATOR = "creator"
    OWNER = "creator"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"
    RESTRICTED = "restricted"
    LEFT = "left"
    KICKED = "kicked"


def InlineKeyboardButton(
    text: str,
    callback_data: Optional[str] = None,
    url: Optional[str] = None,
    api_kwargs: Optional[Dict[str, Any]] = None,
    style: Optional[str] = None,
    **kwargs: Any,
) -> _AiogramIKB:
    if api_kwargs and "style" in api_kwargs and style is None:
        style = api_kwargs["style"]
    return _AiogramIKB(
        text=text,
        callback_data=callback_data,
        url=url,
        style=style,
        **kwargs,
    )


class InlineKeyboardMarkup(_AiogramIKM):
    def __init__(self, inline_keyboard: Any = None, **kwargs: Any) -> None:
        if isinstance(inline_keyboard, list):
            super().__init__(inline_keyboard=inline_keyboard, **kwargs)
        elif "inline_keyboard" in kwargs:
            super().__init__(**kwargs)
        else:
            super().__init__(inline_keyboard=[], **kwargs)


class InputFile:
    def __init__(self, data: Any, filename: str = "file", attach: bool = True) -> None:
        self.data = data
        self.filename = filename
        self.attach = attach


def InputSticker(
    sticker: Any,
    emoji_list: List[str],
    format: str = "static",
    **kwargs: Any,
) -> _AiogramInputSticker:
    if isinstance(sticker, InputFile):
        buf = BufferedInputFile(sticker.data, filename=sticker.filename)
    elif isinstance(sticker, (bytes, bytearray)):
        ext = {"animated": "tgs", "video": "webm", "static": "webp"}.get(format, "webp")
        buf = BufferedInputFile(bytes(sticker), filename=f"sticker.{ext}")
    else:
        buf = sticker
    return _AiogramInputSticker(sticker=buf, emoji_list=emoji_list, format=format, **kwargs)


def _prepare_media(val: Any, default_name: str = "file") -> Any:
    if isinstance(val, (bytes, bytearray)):
        return BufferedInputFile(bytes(val), filename=default_name)
    if isinstance(val, io.IOBase):
        data = val.read()
        name = getattr(val, "name", default_name)
        if not isinstance(name, str) or "/" in name or "\\" in name:
            name = os.path.basename(str(name))
        return BufferedInputFile(data, filename=name)
    return val


# Patch Message methods
async def _reply_text(self: Message, text: str, *args: Any, **kwargs: Any) -> Message:
    kwargs.pop("read_timeout", None)
    kwargs.pop("write_timeout", None)
    quote = kwargs.pop("quote", False)
    if quote:
        return await self.reply(text, *args, **kwargs)
    return await self.answer(text, *args, **kwargs)


async def _reply_html(self: Message, text: str, *args: Any, **kwargs: Any) -> Message:
    kwargs["parse_mode"] = ParseMode.HTML
    return await self.reply_text(text, *args, **kwargs)


async def _reply_photo(self: Message, photo: Any, *args: Any, **kwargs: Any) -> Message:
    kwargs.pop("read_timeout", None)
    kwargs.pop("write_timeout", None)
    photo = _prepare_media(photo, "photo.jpg")
    return await self.answer_photo(photo=photo, *args, **kwargs)


async def _reply_video(self: Message, video: Any, *args: Any, **kwargs: Any) -> Message:
    kwargs.pop("read_timeout", None)
    kwargs.pop("write_timeout", None)
    video = _prepare_media(video, "video.mp4")
    return await self.answer_video(video=video, *args, **kwargs)


async def _reply_voice(self: Message, voice: Any, *args: Any, **kwargs: Any) -> Message:
    kwargs.pop("read_timeout", None)
    kwargs.pop("write_timeout", None)
    voice = _prepare_media(voice, "voice.ogg")
    return await self.answer_voice(voice=voice, *args, **kwargs)


async def _reply_document(self: Message, document: Any, *args: Any, **kwargs: Any) -> Message:
    kwargs.pop("read_timeout", None)
    kwargs.pop("write_timeout", None)
    document = _prepare_media(document, "document.bin")
    return await self.answer_document(document=document, *args, **kwargs)


async def _reply_animation(self: Message, animation: Any, *args: Any, **kwargs: Any) -> Message:
    kwargs.pop("read_timeout", None)
    kwargs.pop("write_timeout", None)
    animation = _prepare_media(animation, "animation.gif")
    return await self.answer_animation(animation=animation, *args, **kwargs)


Message.reply_text = _reply_text
Message.reply_html = _reply_html
Message.reply_photo = _reply_photo
Message.reply_video = _reply_video
Message.reply_voice = _reply_voice
Message.reply_document = _reply_document
Message.reply_animation = _reply_animation
Message.chat_id = property(lambda self: self.chat.id)


# Patch CallbackQuery methods
async def _cb_edit_text(self: CallbackQuery, text: str, *args: Any, **kwargs: Any) -> Any:
    kwargs.pop("read_timeout", None)
    kwargs.pop("write_timeout", None)
    if self.message and isinstance(self.message, Message):
        return await self.message.edit_text(text, *args, **kwargs)
    return None


async def _cb_edit_caption(self: CallbackQuery, caption: str, *args: Any, **kwargs: Any) -> Any:
    kwargs.pop("read_timeout", None)
    kwargs.pop("write_timeout", None)
    if self.message and isinstance(self.message, Message):
        return await self.message.edit_caption(caption, *args, **kwargs)
    return None


async def _cb_edit_markup(self: CallbackQuery, reply_markup: Any = None, *args: Any, **kwargs: Any) -> Any:
    kwargs.pop("read_timeout", None)
    kwargs.pop("write_timeout", None)
    if self.message and isinstance(self.message, Message):
        return await self.message.edit_reply_markup(reply_markup=reply_markup, *args, **kwargs)
    return None


CallbackQuery.edit_message_text = _cb_edit_text
CallbackQuery.edit_message_caption = _cb_edit_caption
CallbackQuery.edit_message_reply_markup = _cb_edit_markup


# Patch File and Document methods
async def _file_download_as_bytearray(self: File) -> bytearray:
    buf = io.BytesIO()
    await self.bot.download_file(self.file_path, destination=buf)
    return bytearray(buf.getvalue())


async def _file_download_to_memory(self: File, out: io.IOBase) -> io.IOBase:
    await self.bot.download_file(self.file_path, destination=out)
    return out


async def _doc_get_file(self: Document) -> File:
    return await self.bot.get_file(self.file_id)


File.download_as_bytearray = _file_download_as_bytearray
File.download_to_memory = _file_download_to_memory
Document.get_file = _doc_get_file


class CompatContext:
    def __init__(
        self,
        bot: Bot,
        bot_data: Dict[str, Any],
        job_queue: Any,
        args: Optional[List[str]] = None,
        application: Any = None,
        job: Any = None,
        error: Any = None,
    ):
        self.bot = bot
        self.bot_data = bot_data
        self.job_queue = job_queue
        self.args = args or []
        self.application = application
        self.job = job
        self.error = error


class CompatUpdate:
    def __init__(
        self,
        event: Any,
        bot: Bot,
        bot_data: Optional[Dict[str, Any]] = None,
        job_queue: Any = None,
    ):
        self.event = event
        self.bot = bot
        self.effective_user = getattr(event, "from_user", None)
        if isinstance(event, Message):
            self.message = event
            self.effective_message = event
            self.effective_chat = event.chat
            self.callback_query = None
            self.my_chat_member = None
            self.pre_checkout_query = None
        elif isinstance(event, CallbackQuery):
            self.message = event.message if isinstance(event.message, Message) else None
            self.effective_message = self.message
            self.effective_chat = self.message.chat if self.message else None
            self.callback_query = event
            self.my_chat_member = None
            self.pre_checkout_query = None
        elif isinstance(event, ChatMemberUpdated):
            self.message = None
            self.effective_message = None
            self.effective_chat = event.chat
            self.callback_query = None
            self.my_chat_member = event
            self.pre_checkout_query = None
        elif isinstance(event, PreCheckoutQuery):
            self.message = None
            self.effective_message = None
            self.effective_chat = None
            self.callback_query = None
            self.my_chat_member = None
            self.pre_checkout_query = event
        else:
            self.message = getattr(event, "message", None)
            self.effective_message = self.message
            self.effective_chat = getattr(event, "chat", None) or (self.message.chat if self.message else None)
            self.callback_query = getattr(event, "callback_query", None)
            self.my_chat_member = getattr(event, "my_chat_member", None)
            self.pre_checkout_query = getattr(event, "pre_checkout_query", None)

    def get_bot(self) -> Bot:
        return self.bot


# Filter implementation matching PTB filters
class BaseFilter:
    def check(self, message: Message) -> bool:
        return True

    def __and__(self, other: Any) -> "AndFilter":
        return AndFilter(self, other)

    def __or__(self, other: Any) -> "OrFilter":
        return OrFilter(self, other)

    def __invert__(self) -> "NotFilter":
        return NotFilter(self)

    async def __call__(self, event: Any) -> bool:
        if isinstance(event, Message):
            return self.check(event)
        if isinstance(event, CallbackQuery) and event.message and isinstance(event.message, Message):
            return self.check(event.message)
        return False


class AndFilter(BaseFilter):
    def __init__(self, f1: Any, f2: Any):
        self.f1 = f1
        self.f2 = f2

    def check(self, message: Message) -> bool:
        c1 = self.f1.check(message) if hasattr(self.f1, "check") else bool(self.f1(message))
        if not c1:
            return False
        return self.f2.check(message) if hasattr(self.f2, "check") else bool(self.f2(message))


class OrFilter(BaseFilter):
    def __init__(self, f1: Any, f2: Any):
        self.f1 = f1
        self.f2 = f2

    def check(self, message: Message) -> bool:
        c1 = self.f1.check(message) if hasattr(self.f1, "check") else bool(self.f1(message))
        if c1:
            return True
        return self.f2.check(message) if hasattr(self.f2, "check") else bool(self.f2(message))


class NotFilter(BaseFilter):
    def __init__(self, f: Any):
        self.f = f

    def check(self, message: Message) -> bool:
        c = self.f.check(message) if hasattr(self.f, "check") else bool(self.f(message))
        return not c


class _TextFilter(BaseFilter):
    def check(self, message: Message) -> bool:
        return message.text is not None


class _CommandFilter(BaseFilter):
    def check(self, message: Message) -> bool:
        text = message.text or message.caption or ""
        return text.startswith("/")


class _PhotoFilter(BaseFilter):
    def check(self, message: Message) -> bool:
        return bool(message.photo)


class _VideoFilter(BaseFilter):
    def check(self, message: Message) -> bool:
        return bool(message.video)


class _AnimationFilter(BaseFilter):
    def check(self, message: Message) -> bool:
        return bool(message.animation)


class _DocumentAllFilter(BaseFilter):
    def check(self, message: Message) -> bool:
        return bool(message.document)


class _AllFilter(BaseFilter):
    def check(self, message: Message) -> bool:
        return True


class _AutomaticForwardFilter(BaseFilter):
    def check(self, message: Message) -> bool:
        return bool(getattr(message, "is_automatic_forward", False))


class _SuccessfulPaymentFilter(BaseFilter):
    def check(self, message: Message) -> bool:
        return bool(message.successful_payment)


class _RegexFilter(BaseFilter):
    def __init__(self, pattern: Union[str, re.Pattern]):
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern

    def check(self, message: Message) -> bool:
        text = message.text or message.caption or ""
        return bool(self.pattern.search(text))


class _CaptionRegexFilter(BaseFilter):
    def __init__(self, pattern: Union[str, re.Pattern]):
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern

    def check(self, message: Message) -> bool:
        text = message.caption or ""
        return bool(self.pattern.search(text))


class _ChatTypeFilters:
    @property
    def PRIVATE(self) -> BaseFilter:
        class _Priv(BaseFilter):
            def check(self, m: Message) -> bool:
                return m.chat.type == ChatType.PRIVATE
        return _Priv()

    @property
    def GROUPS(self) -> BaseFilter:
        class _Grp(BaseFilter):
            def check(self, m: Message) -> bool:
                return m.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)
        return _Grp()


class _StatusUpdateFilters:
    @property
    def NEW_CHAT_MEMBERS(self) -> BaseFilter:
        class _NCM(BaseFilter):
            def check(self, m: Message) -> bool:
                return bool(m.new_chat_members)
        return _NCM()

    @property
    def LEFT_CHAT_MEMBER(self) -> BaseFilter:
        class _LCM(BaseFilter):
            def check(self, m: Message) -> bool:
                return bool(m.left_chat_member)
        return _LCM()

    @property
    def ALL(self) -> BaseFilter:
        class _AllStat(BaseFilter):
            def check(self, m: Message) -> bool:
                return bool(
                    m.new_chat_members
                    or m.left_chat_member
                    or m.pinned_message
                    or m.new_chat_title
                    or m.new_chat_photo
                    or m.delete_chat_photo
                    or m.group_chat_created
                    or m.supergroup_chat_created
                    or m.channel_chat_created
                    or m.message_auto_delete_timer_changed
                    or m.migrate_to_chat_id
                    or m.migrate_from_chat_id
                )
        return _AllStat()


class _DocumentFilters:
    @property
    def ALL(self) -> BaseFilter:
        return _DocumentAllFilter()


class FiltersNamespace:
    TEXT = _TextFilter()
    COMMAND = _CommandFilter()
    PHOTO = _PhotoFilter()
    VIDEO = _VideoFilter()
    ANIMATION = _AnimationFilter()
    ALL = _AllFilter()
    IS_AUTOMATIC_FORWARD = _AutomaticForwardFilter()
    SUCCESSFUL_PAYMENT = _SuccessfulPaymentFilter()
    ChatType = _ChatTypeFilters()
    StatusUpdate = _StatusUpdateFilters()
    Document = _DocumentFilters()

    @staticmethod
    def Regex(pattern: Union[str, re.Pattern]) -> _RegexFilter:
        return _RegexFilter(pattern)

    @staticmethod
    def CaptionRegex(pattern: Union[str, re.Pattern]) -> _CaptionRegexFilter:
        return _CaptionRegexFilter(pattern)


filters = FiltersNamespace()


# Handler definitions matching PTB
class CommandHandler:
    def __init__(
        self,
        commands: Union[str, List[str], Set[str]],
        callback: Callable[..., Any],
        filters: Optional[BaseFilter] = None,
    ):
        if isinstance(commands, str):
            self.commands = {commands.lower()}
        else:
            self.commands = {c.lower() for c in commands}
        self.callback = callback
        self.filters = filters

    def matches(self, message: Message) -> Tuple[bool, List[str]]:
        text = message.text or message.caption or ""
        if not text.startswith("/"):
            return False, []
        parts = text.split()
        cmd_part = parts[0][1:].lower()
        if "@" in cmd_part:
            cmd_part = cmd_part.split("@")[0]
        if cmd_part not in self.commands:
            return False, []
        if self.filters and not self.filters.check(message):
            return False, []
        return True, parts[1:]


class CallbackQueryHandler:
    def __init__(
        self,
        callback: Callable[..., Any],
        pattern: Optional[Union[str, re.Pattern]] = None,
    ):
        self.callback = callback
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern

    def matches(self, cq: CallbackQuery) -> bool:
        data = cq.data or ""
        if self.pattern is None:
            return True
        return bool(self.pattern.search(data))


class MessageHandler:
    def __init__(self, filters: BaseFilter, callback: Callable[..., Any]):
        self.filters = filters
        self.callback = callback

    def matches(self, message: Message) -> bool:
        if self.filters is None:
            return True
        return self.filters.check(message)


class ChatMemberHandler:
    MY_CHAT_MEMBER = "my_chat_member"
    CHAT_MEMBER = "chat_member"

    def __init__(self, callback: Callable[..., Any], chat_member_types: str = MY_CHAT_MEMBER):
        self.callback = callback
        self.chat_member_types = chat_member_types


class PreCheckoutQueryHandler:
    def __init__(self, callback: Callable[..., Any]):
        self.callback = callback


class TypeHandler:
    def __init__(self, type_: Any, callback: Callable[..., Any]):
        self.type = type_
        self.callback = callback


# Application Adapter that manages registration across priority groups
class AiogramApplicationAdapter:
    def __init__(self, bot: Bot, dp: Any, job_queue: Any, bot_data: Dict[str, Any]):
        self.bot = bot
        self.dp = dp
        self.job_queue = job_queue
        self.bot_data = bot_data
        self.handlers: Dict[int, List[Any]] = {}
        self.error_handlers: List[Callable[..., Any]] = []

    def add_handler(self, handler: Any, group: int = 0) -> None:
        self.handlers.setdefault(group, []).append(handler)

    def add_error_handler(self, handler: Callable[..., Any]) -> None:
        self.error_handlers.append(handler)
