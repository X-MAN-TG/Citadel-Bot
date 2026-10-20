from typing import Any

from bot.utils.compat import CallbackQueryHandler, CommandHandler, MessageHandler, filters


def register_user_handlers(app: Any) -> None:
    from bot.handlers.user import (
        afk,
        ai,
        bluff,
        chat_events,
        clans,
        donate,
        economy,
        economy_features,
        extras,
        help as help_module,
        kang,
        lang,
        leaderboard,
        love,
        mafia,
        media,
        menu,
        notes,
        ping,
        profile,
        qextra,
        quote,
        react,
        reel,
        referral,
        shop,
        speak,
        truthdare,
    )
    # 1. Economy basic commands
    app.add_handler(CommandHandler("start", economy.start_command))
    app.add_handler(CommandHandler("wallet", economy.wallet_command))
    app.add_handler(CommandHandler("claim", economy.claim_command))
    app.add_handler(CommandHandler("pay", economy.pay_command))
    app.add_handler(CommandHandler("guard", economy.guard_command))
    app.add_handler(CommandHandler("rob", economy.rob_command))
    app.add_handler(CommandHandler("rankings", economy.rankings_command))
    app.add_handler(CommandHandler("bluff", bluff.bluff_command))

    app.add_handler(CallbackQueryHandler(economy.wallet_command, pattern="^wallet:refresh$"))
    app.add_handler(CallbackQueryHandler(economy.claim_command, pattern="^claim$"))
    app.add_handler(CallbackQueryHandler(economy.rankings_callback, pattern="^rankings:"))
    app.add_handler(CallbackQueryHandler(bluff.bluff_callback, pattern="^bluff:"))
    app.add_handler(CallbackQueryHandler(economy.features_callback, pattern="^features$"))
    app.add_handler(CallbackQueryHandler(economy.games_callback, pattern="^games$"))
    app.add_handler(CallbackQueryHandler(economy.noop_callback, pattern="^noop$"))

    # Media helper
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.ANIMATION | filters.VIDEO | filters.Document.ALL)
        & filters.ChatType.PRIVATE,
        media.file_id_handler,
    ))

    # Economy features (vault, deposit, etc.)
    for cmd, fn in (
        ("vault", economy_features.vault_command),
        ("deposit", economy_features.deposit_command),
        ("withdraw", economy_features.withdraw_command),
        ("work", economy_features.work_command),
        ("spin", economy_features.spin_command),
        ("mafiatop", economy_features.mafiatop_command),
    ):
        app.add_handler(CommandHandler(cmd, fn))

    # Mafia game handlers
    app.add_handler(CommandHandler("mafia", mafia.mafia_command))
    app.add_handler(CallbackQueryHandler(mafia.lobby_callback, pattern="^mafia:(join|start|cancel):"))
    app.add_handler(MessageHandler(
        filters.Regex(r"^/start mafia_") & filters.ChatType.PRIVATE,
        mafia.dm_start_handler,
    ), group=-1)
    app.add_handler(CallbackQueryHandler(mafia.night_callback, pattern="^mn:"))
    app.add_handler(CallbackQueryHandler(mafia.vote_callback, pattern="^mv:"))
    app.add_handler(CallbackQueryHandler(mafia.kamikaze_callback, pattern="^mk:"))
    app.add_handler(CommandHandler("stopmafia", mafia.stop_command))

    # AI chat
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai.ai_chat), group=5)

    # Modular registers
    react.register(app)
    extras.register(app)
    donate.register(app)
    lang.register(app)
    afk.register(app)
    love.register(app)
    quote.register(app)
    menu.register(app)
    speak.register(app)
    clans.register(app)
    kang.register(app)
    qextra.register(app)
    ping.register(app)
    reel.register(app)
    profile.register(app)
    leaderboard.register(app)
    referral.register(app)
    shop.register(app)
    help_module.register(app)
    notes.register(app)
    truthdare.register(app)
    chat_events.register(app)
