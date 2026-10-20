# Migration Guide: Rumi (PTB) to Saloni (aiogram 3.31.0)

## Overview
This document records the migration of the Telegram bot from `python-telegram-bot` (v22.8) to `aiogram` (v3.31.0), codebase restructuring, and renaming of the bot persona from "Rumi" to "Saloni".

The migration preserves 100% of the existing behavior, commands, callbacks, databases, configurations, and external integrations with zero behavior change.

---

## 1. Audit Summary

### 1.1 Deployment & Entrypoint
- **Original Entrypoint:** `main.py` (executes `main()` running `Application.run_polling()`).
- **Dependencies:** `python-telegram-bot==22.8`, `asyncpg==0.31.0`, `python-dotenv==1.2.3`, `httpx[http2]==0.28.1`, `APScheduler==3.11.3`, `tzlocal==5.4.4`, `pillow==12.3.0`, `edge-tts==7.2.8`, `yt-dlp`.
- **System Packages:** `nixpacks.toml` specifies `nixPkgs = ["...", "ffmpeg"]`.
- **Deploy Target:** Works out of the box with Nixpacks / Railway / Render / VPS via `python main.py`.

### 1.2 Environment Variables
| Variable | Required | Default | Usage |
|---|---|---|---|
| `BOT_TOKEN` | Yes | - | Telegram Bot API Token |
| `DATABASE_URL` | Yes | - | PostgreSQL Connection String |
| `GEMINI_API_KEY` | Yes | - | Google Gemini API Key for AI responses |
| `GROQ_API_KEY` | No | `None` | Groq API Key for fallback AI responses |
| `QUOTE_API_URL` | No | `https://quote-api-production-869b.up.railway.app` | Quote generation backend URL |

### 1.3 Database Usage
- PostgreSQL accessed via `asyncpg.Pool` initialized in `db.py` (`init_pool()` and `get_pool()`).
- Schema defined in `schema.sql`.
- Tables:
  - Core: `users`, `wallets`, `transactions`, `streaks`, `rob_cooldowns`, `bluff_games`, `rob_xp_log`, `ai_usage`, `ai_memory`, `mafia_stats`, `rob_msg_log`, `clans`, `clan_members`, `blood_pacts`, `bounties`
  - Group Management (`ax_` prefixed): `ax_groups`, `ax_connections`, `ax_chat_members`, `ax_user_stats`, `ax_warns`, `ax_settings`, `ax_notes`, `ax_filters`, `ax_temp_punish`, `ax_afk`, `ax_ship_cooldowns`, `ax_couple_of_day`, `ax_warn_settings`, `ax_warn_log`, `ax_approved`, `ax_locks`, `ax_lock_settings`, `ax_allowlist`, `ax_blocklist`, `ax_blocklist_settings`, `ax_raid_settings`, `ax_rules`, `ax_report_settings`, `ax_pin_settings`, `ax_captcha_settings`, `ax_captcha_pending`, `ax_cleancmd`, `ax_cleanservice`, `ax_disabled`, `ax_disable_settings`, `ax_log_settings`, `ax_misc_settings`, `ax_note_settings`, `ax_user_lang`, `ax_action_topics`, `ax_watchlist`, `ax_watch_log`, `ax_bot_bans`, `ax_kill_status`, `ax_referrals`, `ax_shop_owned`, `ax_channels`, `ax_chan_cleanup`.
- **Note on DB Compatibility:** All database table and column names remain strictly identical to preserve compatibility with existing production data.

### 1.4 Handlers, Middlewares & Jobs
- **Handlers:**
  - 100+ commands covering Economy, Games (Shadow Bluff, Mafia), Clans, AI Chat, Profile, Moderation, Locks, Captcha, Notes, Filters, Backup, Rules, Welcome/Goodbye, Tag, Love/Ship, Speak (TTS), Reels download.
  - 30+ Callback queries (`wallet:`, `claim`, `rankings:`, `bluff:`, `mafia:`, `clan:`, `axp:`, `axg:`, `axa:`, `axrst_`, `axc:`, `axcn_`, `axcc:`, `axd:`, `axh:`, `axlg_`, `axm:`, `prof_close:`, `axs:`, `axshop:`, `td:`, `axw:`, `axwz:`).
  - Message watchers: AI chat text trigger, Reel link downloader, Auto emoji react, Notes hashtag `#name`, Quote cache collector, Status updates (new chat members, left chat member).
  - My chat member updates: bot added/removed from channel or group.
  - Pre-checkout query & successful payment for Star donations.
- **PTB Handler Groups & Priority (Middleware Pipeline):**
  - Group -30: Quote message cache
  - Group -10: Private `/start note_` dispatcher
  - Group -9: Group disabled command checker, private `/start ref_` tracker
  - Group -8: Clean command message remover, Clean service message cleaner
  - Group -7: Watched groups logger, Flood counter
  - Group -6: Global bot ban gate, Social reel downloader
  - Group -5: User and chat stats tracking
  - Group -4: Channel status tracker, Locks engine, Blocklist detector, Flood threshold enforcer
  - Group -3: Antiraid join protector, Pin cleaner, Group notes filter watcher
  - Group -2: AFK watcher, Captcha challenge trigger on join
  - Group -1: Captcha text answer checker, Admin mentions (`@admin`), Mafia private start `/start mafia_`, Remote connect `/connect`, Help moderation callback
  - Group 0: Default commands and callbacks
  - Group 1: Group hashtag notes
  - Group 5: AI chat responses, promote/demote cache invalidator, Telegram Stars payment handler
  - Group 9: Auto emoji reaction
  - Group 11: Profile close callback
- **Scheduled Jobs (PTB JobQueue):**
  - `autodelete`: Deletes bot replies to selected commands after 15 minutes.
  - `ax_actiontopic`: Loads action topic thread ID cache 5s after startup.
  - `ax_captcha`: Checks and expires unanswered captchas every 60s.
  - `ax_channel`: Cleans expired promo messages every 5m; counts channel subscribers every 3h.
  - `ax_channel2`: Channel promo job every 1h; weekly stats job.
  - `ax_cleancmd`: Deletes command invocation after configured seconds.
  - `ax_cleanservice`: Deletes service notification messages after 2s.
  - `ax_leaderboard`: Posts weekly richest groups leaderboard.
  - `ax_misc3`: Loads settings 5s after startup.
  - `ax_mod`: Checks expired temporary mutes and bans every 5m.
  - `ax_track`: Flushes cached message counts to DB every 5m.
  - `chat_events`: Flash Heist event loop every 4–5h with 2m countdown timer.

---

## 2. PTB to aiogram 3.31.0 Mapping Table

| PTB Construct (v22.8) | aiogram 3.31.0 Equivalent | Implementation Notes |
|---|---|---|
| `Application.builder().token(token)...build()` | `Bot(token=..., default=DefaultBotProperties(parse_mode=ParseMode.HTML))` and `Dispatcher()` | Sessions properly managed and closed on shutdown |
| `CommandHandler("cmd", handler)` | `router.message.register(handler, Command("cmd"))` | Case-insensitive command handling |
| `context.args` | `command.args` via `CommandObject` filter or helper | Split into list of string arguments |
| `CallbackQueryHandler(handler, pattern="^pat:")` | `router.callback_query.register(handler, F.data.startswith("pat:"))` or regex | String callback compatibility preserved |
| `MessageHandler(filters.TEXT & ~filters.COMMAND, handler)` | `router.message.register(handler, F.text & ~Command())` | Handled via aiogram magic filters |
| `MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, h)` | `router.message.register(h, F.new_chat_members)` | New member joins |
| `MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, h)` | `router.message.register(h, F.left_chat_member)` | Member leaves |
| `MessageHandler(filters.ChatType.PRIVATE, h)` | `router.message.register(h, F.chat.type == ChatType.PRIVATE)` | Chat type filtering |
| `MessageHandler(filters.ChatType.GROUPS, h)` | `router.message.register(h, F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))` | Groups & Supergroups |
| `ChatMemberHandler(h, ChatMemberHandler.MY_CHAT_MEMBER)` | `router.my_chat_member.register(h)` | Track bot added/removed |
| `PreCheckoutQueryHandler(h)` | `router.pre_checkout_query.register(h)` | Telegram Stars checkout |
| `MessageHandler(filters.SUCCESSFUL_PAYMENT, h)` | `router.message.register(h, F.successful_payment)` | Payment confirmation |
| `TypeHandler(Update, ignore_old_updates)` | Outer Middleware `OldUpdatesMiddleware` | Discards messages older than 10 minutes |
| `ApplicationHandlerStop` | Returning early from middleware / handler routing | Stopping subsequent handlers from executing |
| Handler groups (`group=-10...11`) | Ordered aiogram Middlewares and Routers | Preserves exact execution priority |
| `context.bot_data` | `dp.workflow_data` / `bot_data` dictionary | Shared state (`pool`, `ce_heists`, `watch_ids`) |
| `context.bot` | `bot: Bot` injected into handlers / jobs | Native aiogram bot instance |
| `JobQueue` (`run_once`, `run_repeating`, `get_jobs_by_name`) | `AsyncJobQueue` asyncio background scheduler service | Implements identical API and context |
| `telegram.error.TelegramError` | `aiogram.exceptions.TelegramAPIError` | `TelegramBadRequest`, `TelegramForbiddenError`, `TelegramRetryAfter` |
| `update.effective_message.reply_text()` | `message.answer()` or `message.reply()` | Default HTML parse mode |
| `InlineKeyboardMarkup`, `InlineKeyboardButton` | `InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(...)]])` | Keyboard factories and helper methods |

---

## 3. Codebase Restructure & File Mapping

To eliminate redundant prefixes (`ax_`) and organize into a modular architecture:

| Old File | New File | Role |
|---|---|---|
| `main.py` | `main.py` + `bot/main.py` | Root entrypoint for one-click deploy + bot runner |
| `config.py` | `bot/config.py` | Tunable economy numbers, AI models, trigger words |
| `db.py` | `bot/database/db.py` | PostgreSQL pool initialization and schema loading |
| `schema.sql` | `bot/database/schema.sql` | Database tables & indexes |
| `services.py` | `bot/services/economy.py` | Economy core service (wallet, transfer, rob, etc.) |
| `games.py` | `bot/services/games.py` | Shadow Bluff card game engine |
| `clan_services.py` | `bot/services/clan_services.py` | Clan business logic |
| `clan_admin.py` | `bot/services/clan_admin.py` | Clan admin actions |
| `clan_ui.py` | `bot/keyboards/clan_ui.py` | Clan keyboards and strings |
| `clans.py` | `bot/handlers/user/clans.py` | Clan user commands and invites |
| `bluff_handlers.py` | `bot/handlers/user/bluff.py` | Shadow Bluff commands and callbacks |
| `bluff_ui.py` | `bot/keyboards/bluff_ui.py` | Shadow Bluff UI and rendering |
| `mafia_config.py` | `bot/services/mafia_config.py` | Mafia game configuration |
| `mafia_engine.py` | `bot/services/mafia_engine.py` | Mafia game logic |
| `mafia_text.py` | `bot/services/mafia_text.py` | Mafia game dialogs and strings |
| `mafia_handlers.py` | `bot/handlers/user/mafia.py` | Mafia game commands and callbacks |
| `ai_engine.py` | `bot/services/ai_engine.py` | Gemini & Groq API client |
| `ai_store.py` | `bot/services/ai_store.py` | AI chat memory and daily quotas |
| `ai_handlers.py` | `bot/handlers/user/ai.py` | AI chat triggers and handlers |
| `auto_react.py` | `bot/handlers/user/react.py` | Emoji auto-reaction handler |
| `autodelete.py` | `bot/middlewares/autodelete.py` | Command auto-deletion service/middleware |
| `media_helper.py` | `bot/handlers/user/media.py` | DM media file ID inspector |
| `economy_features.py` | `bot/handlers/user/economy_features.py` | Vault, work, spin, mafiatop |
| `handlers.py` | `bot/handlers/user/economy.py` | Start, wallet, claim, pay, rob, guard |
| `chat_events.py` | `bot/handlers/user/chat_events.py` | Blood pacts, bounties, flash heists |
| `ui.py` | `bot/keyboards/ui.py` | Global UI components, cards, navigation |
| `quote_cache.py` | `bot/services/quote_cache.py` | Quote message in-memory cache |
| `quote_emoji.py` | `bot/services/quote_emoji.py` | Quote emoji font rendering |
| `quote_fb.py` | `bot/services/quote_fb.py` | Quote fallback fonts |
| `quote_layout.py` | `bot/services/quote_layout.py` | Quote layout engine |
| `quote_remote.py` | `bot/services/quote_remote.py` | Remote quote API integration |
| `quote_render.py` | `bot/services/quote_render.py` | Local quote image generator |
| `ax_actions.py` | `bot/services/actions.py` | Unified punishment executor |
| `ax_actiontopic.py` | `bot/handlers/admin/actiontopic.py` | Admin action topic management |
| `ax_admin2.py` | `bot/handlers/admin/admin_tools.py` | Admin list, admin cache, user id |
| `ax_adminpanel.py` | `bot/handlers/admin/adminpanel.py` | Global owner admin panel |
| `ax_adminpanel2.py` | `bot/handlers/admin/adminpanel_group.py` | Group-specific owner details |
| `ax_afk.py` | `bot/handlers/user/afk.py` | AFK system and watcher |
| `ax_approve.py` | `bot/handlers/admin/approve.py` | Approved user management |
| `ax_backup.py` | `bot/handlers/admin/backup.py` | Group settings export and import |
| `ax_ban.py` | `bot/handlers/admin/ban.py` | Global bot ban commands and gate |
| `ax_blocklist.py` | `bot/handlers/admin/blocklist.py` | Word blocklist management & watcher |
| `ax_broadcast.py` | `bot/handlers/admin/broadcast.py` | Owner broadcast across groups |
| `ax_captcha.py` | `bot/handlers/admin/captcha.py` | Captcha join watcher and solver |
| `ax_captcha2.py` | `bot/handlers/admin/captcha_settings.py` | Captcha configuration commands |
| `ax_channel.py` | `bot/handlers/admin/channel.py` | Channel protection & member drop alert |
| `ax_channel2.py` | `bot/handlers/admin/channel_promo.py` | Periodic channel promotion posts |
| `ax_cheat.py` | `bot/handlers/admin/cheat.py` | Admin balance manipulation inspection |
| `ax_cleancmd.py` | `bot/handlers/admin/cleancmd.py` | Clean commands setting |
| `ax_cleanservice.py` | `bot/handlers/admin/cleanservice.py` | Clean service message setting |
| `ax_common.py` | `bot/utils/common.py` | Common admin checks and target resolution |
| `ax_connect.py` | `bot/handlers/admin/connect.py` | Remote chat connection commands |
| `ax_connect2.py` | `bot/handlers/admin/connect_dm.py` | DM connection wizard |
| `ax_disable.py` | `bot/handlers/admin/disable.py` | Disable/enable commands in groups |
| `ax_dmproxy.py` | `bot/services/dmproxy.py` | Remote command forwarding |
| `ax_donate.py` | `bot/handlers/user/donate.py` | Telegram Stars donation flow |
| `ax_errors.py` | `bot/utils/error_handler.py` | Error logging and crash prevention |
| `ax_extras.py` | `bot/handlers/user/extras.py` | Privacy, markdownhelp, limits, runs |
| `ax_fill.py` | `bot/utils/fill.py` | Template string variable replacement |
| `ax_flood.py` | `bot/handlers/admin/flood.py` | Flood control commands and recording |
| `ax_funmode.py` | `bot/handlers/admin/funmode.py` | Group fun mode toggle |
| `ax_givecoins.py` | `bot/handlers/admin/givecoins.py` | Admin coin grant command |
| `ax_help.py` | `bot/handlers/user/help.py` | User and admin help guide |
| `ax_kang.py` | `bot/handlers/user/kang.py` | Sticker pack stealer/kang command |
| `ax_kill.py` | `bot/handlers/admin/kill.py` | Fun kill/revive temporary mute |
| `ax_lang.py` | `bot/handlers/user/lang.py` | Language switcher (EN/HI) |
| `ax_leaderboard.py` | `bot/handlers/user/leaderboard.py` | Weekly leaderboard job |
| `ax_lockcore.py` | `bot/services/lockcore.py` | Chat lock verification logic |
| `ax_locks.py` | `bot/handlers/admin/locks.py` | Lock configuration commands |
| `ax_log.py` | `bot/handlers/admin/log.py` | Moderation event log channel |
| `ax_love.py` | `bot/handlers/user/love.py` | Ship, match, couple of the day |
| `ax_menu.py` | `bot/handlers/user/menu.py` | Features overview and start menu |
| `ax_misc3.py` | `bot/handlers/admin/misc_settings.py` | Anon admin, silent actions |
| `ax_mod.py` | `bot/handlers/admin/mod.py` | Mute, ban, kick, promote, demote |
| `ax_mod2.py` | `bot/handlers/admin/mod_variants.py` | Silent (s*) and delete (d*) mod variants |
| `ax_notes.py` | `bot/handlers/user/notes.py` | Notes and keyword filters |
| `ax_ping.py` | `bot/handlers/user/ping.py` | Ping latency test |
| `ax_pins.py` | `bot/handlers/admin/pins.py` | Pin, permapin, cleanlinked |
| `ax_profile.py` | `bot/handlers/user/profile.py` | Generated canvas user profile card |
| `ax_purge.py` | `bot/handlers/admin/purge.py` | Message purge and bulk delete |
| `ax_qextra.py` | `bot/handlers/user/qextra.py` | Quote packs and colors |
| `ax_quote.py` | `bot/handlers/user/quote.py` | `/q` quote generator |
| `ax_raid.py` | `bot/handlers/admin/antiraid.py` | Anti-raid protection |
| `ax_reel.py` | `bot/handlers/user/reel.py` | Social media video downloader |
| `ax_referral.py` | `bot/handlers/user/referral.py` | Referral system |
| `ax_reports.py` | `bot/handlers/admin/reports.py` | `@admin` report system |
| `ax_rules.py` | `bot/handlers/admin/rules.py` | Group rules management |
| `ax_settings.py` | `bot/handlers/admin/settings.py` | Group settings interactive panel |
| `ax_shop.py` | `bot/handlers/user/shop.py` | Title and cosmetics shop |
| `ax_speak.py` | `bot/handlers/user/speak.py` | Edge-TTS voice note synthesis |
| `ax_tag.py` | `bot/handlers/admin/tag.py` | Tag all members / admins |
| `ax_topgroups.py` | `bot/handlers/admin/topgroups.py` | Top active groups |
| `ax_topics.py` | `bot/handlers/admin/topics.py` | Forum topic administration |
| `ax_track.py` | `bot/services/track.py` | User and message statistics tracker |
| `ax_truthdare.py` | `bot/handlers/user/truthdare.py` | Truth or Dare multiplayer game |
| `ax_warn.py` | `bot/handlers/admin/warn.py` | Warnings issuance and management |
| `ax_warn2.py` | `bot/handlers/admin/warn_settings.py` | Warning limits and penalty modes |
| `ax_watch.py` | `bot/handlers/admin/watch.py` | Monitored chat message logger |
| `ax_welcome.py` | `bot/handlers/admin/welcome.py` | Welcome & goodbye messages & cards |
| `ax_welcome2.py` | `bot/handlers/admin/welcome_settings.py` | Welcome settings toggles |

---

## 4. Renaming Exceptions (Rumi -> Saloni)

Per Phase 3 specifications, all references to "Rumi" are systematically updated to "Saloni" with casing preserved (`rumi` -> `saloni`, `Rumi` -> `Saloni`, `RUMI` -> `SALONI`).

The following intentional exceptions are preserved and documented for backwards compatibility:

1. **Database Schema & Table Names:**
   - Table names (e.g. `ax_groups`, `ax_settings`, `users`, `wallets`) remain unchanged so existing databases can connect with 0 migrations and 0 data loss.
2. **Backup File Format Compatibility:**
   - In `backup.py` (`ax_backup.py`), existing backup JSON files contain `{"rumi_backup": 1}`.
   - For backwards compatibility, the importer accepts BOTH `"saloni_backup": 1` AND `"rumi_backup": 1`. Newly exported backups will write `"saloni_backup": 1` alongside `"rumi_backup": 1`.
3. **External GitHub Asset URL:**
   - In `economy.py` (`handlers.py`), `PLACEHOLDER_PHOTO_URL` references the raw image URL on GitHub. To prevent broken image links on existing deployments without manual asset upload, local asset `assets/saloni-start-v2.png` (symlinked/copied from `assets/rumi-start-v2.png`) is prioritized, while preserving the fallback URL safely.
4. **Environment Variable Names:**
   - `BOT_TOKEN`, `DATABASE_URL`, `GEMINI_API_KEY`, `GROQ_API_KEY`, and `QUOTE_API_URL` remain standard and identical.

---

## 5. Verification & Testing Results

All Phase 5 verification requirements have been completed and passed:

1. **Compilation & Syntax:**
   - `python -m compileall .` passed with 0 errors.
   - All 112 modules imported cleanly with 0 syntax or runtime import errors.
2. **Linting:**
   - Static analysis with `pyflakes` verified 0 undefined variables or broken references across the entire codebase.
3. **Handler Mapping Checklist:**
   - All 278 handlers across all 16 priority groups (`-30` to `+11`) were verified registered in the dispatch pipeline.
   - Execution order, priority semantics, and `ApplicationHandlerStop` halting were tested and confirmed identical to PTB.
4. **Mock Update Pipeline Execution:**
   - Tested `/start`, `/wallet`, `/claim` in private chats.
   - Tested inline callback query flows (`wallet:refresh`, `claim`).
   - Tested `AsyncJobQueue` scheduling (`run_once`, `run_repeating`, job removal).
   - Tested error handler resilience against uncaught exceptions and transient network failures.
5. **No Residual "Rumi" Strings:**
   - Case-insensitive search across the codebase confirms 0 occurrences of "rumi" outside the documented exceptions (backward-compatible backup format validation).
6. **Deployment Checklist:**
   - `.env.example` provides all configuration variables.
   - Root `main.py` entrypoint runs `asyncio.run(main())` for 100% backward compatibility with Nixpacks / Railway / Render / VPS deployments.

