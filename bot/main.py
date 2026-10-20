import asyncio
import logging
import os
from typing import Any

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update

from bot.database import db
from bot.handlers.admin import register_admin_handlers
from bot.handlers.admin import ban
from bot.handlers.user import register_user_handlers
from bot.middlewares.autodelete import install as install_autodelete
from bot.middlewares.pipeline import handle_update
from bot.services.games import refund_unfinished
from bot.services.scheduler import AsyncJobQueue
from bot.utils.compat import AiogramApplicationAdapter
from bot.utils.error_handler import register as register_error_handler

load_dotenv()

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.INFO)

log = logging.getLogger(__name__)


async def main() -> None:
    token = os.environ["BOT_TOKEN"]

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    pool = await db.init_pool()

    bot_data: dict[str, Any] = {
        "pool": pool,
        "ce_heists": {},
        "watch_ids": set(),
    }

    job_queue = AsyncJobQueue(bot=bot, bot_data=bot_data)
    app = AiogramApplicationAdapter(bot=bot, dp=dp, job_queue=job_queue, bot_data=bot_data)

    await ban._load(pool)
    refunded = await refund_unfinished(pool)
    if refunded:
        print(f"Refunded {refunded} unfinished Shadow Bluff game(s).")

    register_error_handler(app)
    register_user_handlers(app)
    register_admin_handlers(app)
    install_autodelete(app)

    @dp.update()
    async def _update_receiver(update: Update) -> None:
        await handle_update(update, bot, app)

    print("Saloni is running (long polling). Press Ctrl+C to stop.")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "edited_message",
                "callback_query",
                "chat_member",
                "my_chat_member",
                "pre_checkout_query",
            ],
        )
    finally:
        job_queue.stop()
        await bot.session.close()
        await pool.close()
        print("Saloni has stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
