# Saloni Telegram Bot

A comprehensive, production-ready Telegram bot built with **aiogram 3.31.0** and **PostgreSQL (asyncpg)**.

## Features

- **Economy System**: Wallets, daily claims, work, rob with guards, bounties, vault deposits, and global rankings.
- **Card Games & Mini-Games**:
  - **Shadow Bluff**: Interactive card bluffing game with custom card rendering and betting.
  - **Mafia**: Complete multiplayer Mafia game with roles (Detective, Doctor, Kamikaze, etc.), day/night phases, and voting.
  - **Truth or Dare**: Multiplayer group game.
- **Clans & Guilds**: Form clans, recruit members, declare clan wars, and forge blood pacts.
- **Full Group Moderation**:
  - Mute, Ban, Kick, Warn (with configurable thresholds and actions).
  - Silent (`/sban`, `/smute`) and Delete (`/dban`, `/dmute`) variants.
  - Anti-Raid system & Captcha verification on entry (math/button).
  - Locks engine (stickers, media, links, forwards, voice, etc.).
  - Automated flood detection and punishment.
  - Auto-cleaning for commands and service notifications.
- **AI Persona**:
  - Interactive conversational assistant powered by Google Gemini (with Groq fallback).
  - Configurable trigger words (e.g., `saloni`).
- **Media & Utilities**:
  - Quote Generator (`/q` and `/qpack`) with custom layouts, colors, and remote API support.
  - Video and Reels downloader (Instagram, TikTok, YouTube).
  - Edge-TTS Voice synthesis (`/speak`).
  - Welcome & Goodbye messages with custom format tags and canvas card images.
  - Group settings backup export/import.

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Google Gemini API Key (optional, for AI features)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd rumi-bot-main
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Copy `.env.example` to `.env` and fill in your values:
   ```bash
   BOT_TOKEN=123456789:ABCDEF...
   DATABASE_URL=postgresql://user:password@localhost:5432/salonidb
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Run the bot:**
   ```bash
   python main.py
   ```

---

## Deployment

The bot is ready for one-click deployment on **Railway**, **Render**, **Heroku**, or **VPS**:
- **Entrypoint:** `python main.py`
- Built-in `nixpacks.toml` includes system dependencies (`ffmpeg`).

---

## Architecture

```
bot/
├── main.py              # Application entrypoint & update dispatcher
├── config.py            # Economy values, triggers, limits
├── database/            # Database pool & SQL schema
│   ├── db.py
│   └── schema.sql
├── handlers/
│   ├── admin/           # Moderation, locks, warns, anti-raid, etc.
│   └── user/            # Economy, mafia, games, clans, AI chat, quotes
├── keyboards/           # Inline keyboards (UI, clans, bluff)
├── middlewares/         # Update pipeline, old update filter, autodelete
├── services/            # Economy, card engines, AI clients, quote rendering, scheduler
└── utils/               # Compatibility layer, common helpers, error handlers
```
