# Citadel Bot

An all-in-one Telegram group management & community bot built on **python-telegram-bot** — moderation, locks, captcha, greetings, economy & clans, games (Shadow Bluff / Mafia), AI chat, quotes, and more.

## Project Structure

```
Citadel-Bot/
├── core/                 # Entry point & app core (config, db, handlers, services, UI, schema)
├── modules/
│   ├── admin/            # Admin panels, locks core, connect, menu, settings, topics
│   ├── moderation/       # Ban, blocklist, flood, purge, raid, reports, warns, watch
│   ├── greetings/        # Welcome messages & captcha system
│   ├── community/        # AFK, approve, notes, ping, rules, tags, auto-react, autodelete
│   ├── fun/              # Fun mode, kang, love, quotes, reels, speak
│   ├── games/            # Shadow Bluff & Mafia game engines/handlers
│   ├── economy/          # Wallet features, coins, clans, leaderboard, referrals
│   ├── ai/               # AI engine, handlers & store
│   └── misc/             # Actions, backup, broadcast, help, pins, profile
├── assets/
│   ├── fonts/            # Bundled fonts
│   └── media/            # Test images/videos
└── data/
    └── emoji_cache/      # Cached emoji renders
```

## Setup

```bash
pip install -r core/requirements.txt
# Set BOT_TOKEN (and other env vars) in a .env file
python core/main.py
```

## Configuration

- `core/config.py` — bot configuration
- `core/schema.sql` — PostgreSQL database schema (asyncpg)
- `nixpacks.toml` — deployment config (requires `ffmpeg`)
