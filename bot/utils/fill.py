"""Rose-style fillings, random replies and buttons."""
import random
import re
from typing import Any, Dict, List, Optional, Tuple

from bot.utils.common import esc
from bot.utils.compat import InlineKeyboardButton, InlineKeyboardMarkup

BTN = re.compile(
    r"\[([^\]]+)\]\(buttonurl://([^)\s]+?)((?::(?:same|blue|green|red))*)\)"
)
STYLES = {"blue": "primary", "green": "success", "red": "danger"}
FLAGS = ("{preview}", "{nonotif}", "{protect}", "{mediaspoiler}")


def pick(text: Optional[str]) -> str:
    """Choose one random reply when text uses %%% separators."""
    parts = [p.strip() for p in (text or "").split("%%%") if p.strip()]
    return random.choice(parts) if parts else ""


def parse(text: str) -> Tuple[str, List[List[Tuple[str, str, Optional[str]]]], Dict[str, bool]]:
    """Split raw text into (body, rows, flags). Buttons marked :same share a row."""
    rows: List[List[Tuple[str, str, Optional[str]]]] = []
    for m in BTN.finditer(text):
        label, url, opts = m.group(1), m.group(2), m.group(3) or ""
        words = [w for w in opts.split(":") if w]
        style = None
        for w in words:
            if w in STYLES:
                style = STYLES[w]
        item = (label, url, style)
        if "same" in words and rows:
            rows[-1].append(item)
        else:
            rows.append([item])
    body = BTN.sub("", text)
    flags = {f.strip("{}"): (f in body) for f in FLAGS}
    for f in FLAGS:
        body = body.replace(f, "")
    return body.strip(), rows, flags


def fill(body: str, user: Any, chat: Any, rules_link: Optional[str] = None) -> str:
    """Replace fillings. Old {first_name} and {chat_name} keep working."""
    first = esc(user.first_name or "")
    last = esc(user.last_name or "")
    full = (first + " " + last).strip()
    uname = "@" + user.username if user.username else first
    chat_name = esc(chat.title or "this group") if chat else "this group"
    mention = '<a href="tg://user?id=%d">%s</a>' % (user.id, first or "friend")
    table = {
        "{first}": first,
        "{first_name}": first,
        "{last}": last,
        "{fullname}": full,
        "{username}": esc(uname),
        "{mention}": mention,
        "{id}": str(user.id),
        "{chatname}": chat_name,
        "{chat_name}": chat_name,
    }
    for k, v in table.items():
        body = body.replace(k, v)
    if rules_link:
        body = body.replace("{rules}", "").replace("{rules:same}", "")
    return body


def has_rules(text: str) -> bool:
    return "{rules}" in text or "{rules:same}" in text


def keyboard(
    rows: List[List[Tuple[str, str, Optional[str]]]],
    rules_url: Optional[str] = None,
    rules_same: bool = False,
    note_url: Optional[Any] = None,
) -> Optional[InlineKeyboardMarkup]:
    """Build an InlineKeyboardMarkup from parsed rows."""
    out = []
    for r in rows:
        line = []
        for label, url, style in r:
            if url.startswith("#") and note_url:
                url = note_url(url[1:])
            kw = {"style": style} if style else {}
            line.append(InlineKeyboardButton(text=label, url=url, **kw))
        out.append(line)
    if rules_url:
        b = InlineKeyboardButton(text="📜 Rules", url=rules_url)
        if rules_same and out:
            out[-1].append(b)
        else:
            out.append([b])
    return InlineKeyboardMarkup(inline_keyboard=out) if out else None
