# Telegram Self-Bot

A production-grade Telegram self-bot that runs on your own personal Telegram account.
It provides message management, auto-reply, AI integration, reminders, network/utility
tools, converters, and full profile automation with a clean, testable architecture.

Built with Python 3.12+, Telethon, SQLAlchemy 2.x (async) over SQLite, APScheduler,
yt-dlp, httpx, and pydantic.

## Features

- **Message management** — delete old messages (by age or count) and delete messages by keyword/regex with safe batching and FloodWait handling.
- **Auto reply** — enable/disable, a static default response, and keyword rules with priority, cooldown, regex, exact/contains matching, per-user cooldown, and allowed/blocked chat filters.
- **AI integration** — provider-independent layer (OpenAI-compatible); optional AI auto-reply with context, custom prompt, usage limits and cooldown; AI-generated bios and usernames.
- **Reminders** — one-time (relative or absolute date/time), daily, weekly, and monthly recurrences that persist across restarts; list, delete, and snooze.
- **Downloader** — `/dl <url>` via yt-dlp with queue, progress, size/timeout limits, temporary-file cleanup, and upload back to Telegram.
- **Utility tools** — JSON (format/validate), Base64, URL encode/decode, UUID, hashes, regex tester, timestamp/unix time, JWT decoder, URL shortener, QR, barcode, color converter, Markdown↔HTML, text→QR, and URL screenshots.
- **Network tools** — ping, DNS lookup, IP lookup, WHOIS, HTTP status, SSL certificate info, uptime, and headers — all behind strict SSRF protection.
- **Calculator & time** — safe-expression calculator (no `eval`), stopwatch, timer, random number/choice, secure password generator.
- **Converters** — units, currency (cached), timezone across `zoneinfo`, weather (cached), date calculator, age, and BMI.
- **Profile automation** — set bio, auto bio, time-based bios, current-time bio (clock), online-status bio, random bio rotation, username generator, AI/profile-photo generation, and profile backup/restore with confirmation.
- **Permissions & safety** — owner-only commands, allowed/blocked chat lists, per-command permissions, confirmation for destructive actions, rate limiting, and secret-safe logging.

## Requirements

- Python 3.12 or newer (developed and tested on 3.14)
- A Telegram user account with `api_id` / `api_hash` from [my.telegram.org](https://my.telegram.org)

## Installation

```powershell
# 1) Create and activate a virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Install the package with dev tooling (and optional screenshot support)
pip install -e ".[dev,screenshot]"

# 3) Configure it
Copy-Item .env.example .env
# then edit .env and fill in API_ID and API_HASH
```

On first login the bot asks for your phone number and a verification code.
A Telegram session file (not a password) is stored locally so you stay logged in.

## Configuration

Copy `.env.example` to `.env` and set at least:

```env
API_ID=123456
API_HASH=abcdef0123456789abcdef0123456789
OWNER_ID=your_numeric_user_id
```

Important options:

| Variable | Default | Description |
| --- | --- | --- |
| `API_ID` / `API_HASH` | — | Telegram app credentials (required) |
| `SESSION_NAME` | `selfbot` | Session file name |
| `SESSION_STRING` | empty | Optional pre-exported session string |
| `OWNER_ID` | empty | Your numeric user id (owner-only checks) |
| `COMMAND_PREFIX` | `/` | Command prefix |
| `TIMEZONE` | `Asia/Tehran` | Display/scheduling timezone |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/app.db` | SQLAlchemy database URL |
| `AI_PROVIDER` / `AI_API_KEY` / `AI_MODEL` | empty | Leave empty to disable AI |
| `AI_API_BASE` | empty | Optional custom OpenAI-compatible base URL |
| `DOWNLOAD_DIR` | `downloads` | yt-dlp output directory |
| `MAX_DOWNLOAD_SIZE_MB` | `500` | Maximum download size |
| `DOWNLOAD_TIMEOUT` | `300` | Download timeout (seconds) |
| `WEATHER_API_KEY` | empty | Optional weather provider key |
| `URL_SHORTENER_API_KEY` | empty | Optional URL-shortener provider key |
| `LOG_LEVEL` | `INFO` | Log level |
| `REQUIRE_CONFIRMATION` | `true` | Ask for confirmation before destructive/profile changes |

Never commit `.env` or session files.

## Running

```powershell
python -m selfbot.app
```

If credentials are missing the bot exits with a clear Persian error message.

## Commands

Send commands to your own messages (Saved Messages) or in chats where the bot
is permitted. All responses are in Persian.

### Help & permissions

| Command | Description |
| --- | --- |
| `/help` / `/help <section>` | Show help (e.g. `/help reminder`, `/help network`, `/help <command>`) |
| `/owneronly on/off` | Restrict all commands to owner chats |
| `/allowchat <chat-id>` / `/denychat <chat-id>` | Add/remove a chat from the allowlist / blocklist |
| `/allowlist` / `/chatperms` | Show chat permissions |

### Message management

| Command | Description |
| --- | --- |
| `/del 100` | Delete the last 100 messages of the current chat |
| `/delold 30` / `/delold 7d` | Delete your messages older than a count/duration |
| `/delword spam,scam` / `/delword spam --limit 100` | Delete messages containing keywords (regex option) |

### Auto reply & AI

| Command | Description |
| --- | --- |
| `/autoreply on` / `/autoreply off` / `/autoreply set <msg>` | Toggle and set the default reply |
| `/arule add <keyword> => <reply>` / `/arule list` / `/arule remove <id>` | Keyword reply rules |
| `/ai on` / `/ai off` / `/ai setprompt <prompt>` | Toggle and configure AI auto-reply |

### Reminders

| Command | Description |
| --- | --- |
| `/remind 20m با مشتری تماس بگیر` | One-time reminder (relative) |
| `/remind 2026-10-01 18:30 جلسه` | One-time reminder (absolute date/time) |
| `/remind daily 09:00 ورزش` | Daily reminder |
| `/remind weekly mon 09:00 جلسه هفتگی` | Weekly reminder |
| `/remind monthly 1 10:00 پرداخت قبض` | Monthly reminder |
| `/reminders` | List reminders |
| `/reminddel <id>` | Delete a reminder |
| `/snooze <id> <duration>` | Snooze a one-time reminder (e.g. `/snooze 12 30m`) |

### Utility tools

| Command | Description |
| --- | --- |
| `/json format` / `/json validate` | JSON formatting/minification/validation |
| `/b64 encode <text>` / `/b64 decode <data>` | Base64 encode/decode |
| `/urlencode <text>` / `/urldecode <text>` | URL encode/decode |
| `/uuid` / `/uuid 5` | Generate UUIDs |
| `/hash sha256 <text>` | MD5/SHA1/SHA256/SHA512 hash |
| `/regex <pattern> <text>` | Regex test: matches, groups, positions |
| `/timestamp` / `/timestamp 2026-10-01 12:00` | Timestamp conversion |
| `/unixtime` / `/unixtime 1750000000` | Current/inverse Unix time |
| `/jwt <token>` | Decode a JWT header/payload (never verifies signature) |
| `/short <url>` | URL shortener |
| `/qr <text>` | Generate a QR image |
| `/textqr <text>` | Text → QR image |
| `/barcode 123456789` | Generate a barcode image |
| `/color <value>` | HEX / RGB / HSL color conversion |
| `/mdhtml <text>` / `/htmlmd <html>` | Markdown↔HTML conversion |
| `/ss <url>` | Screenshot of a URL (SSRF-protected, viewport-configurable) |

### Network tools

| Command | Description |
| --- | --- |
| `/ping <host>` | ICMP/HTTP latency and packet-loss check |
| `/dns <domain>` | DNS resolution and records |
| `/ip <host>` | Resolve and inspect addresses |
| `/whois <domain>` | WHOIS lookup |
| `/statusurl <url>` | HTTP status check |
| `/ssl <host>` | SSL/TLS certificate info |
| `/uptime <url>` | Uptime/reachability check |
| `/headers <url>` | Response headers |

All network commands run through SSRF protection and resolve destinations safely.

### Calculator & time

| Command | Description |
| --- | --- |
| `/calc 12 * (5 + 2)` | Safe math expression |
| `/stopwatch start/stop/reset` | Stopwatch |
| `/timer 10m` / `/timer 30s` | Timer |
| `/random 1 100` | Random number |
| `/choose pizza,burger,pasta` | Random choice |
| `/password 20` | Secure password (Python `secrets`) |

### Converters

| Command | Description |
| --- | --- |
| `/convert 10 km mile` / `/convert 100 c f` | Units (length, weight, temperature, time, data size) |
| `/currency 100 USD EUR` | Currency conversion (cached rates) |
| `/tz 15:00 Europe/Tehran America/New_York` | Timezone conversion |
| `/weather تهران` | Weather (cached) |
| `/datecalc 2026-10-01 + 30d` | Date arithmetic (d/w/m/y) |
| `/age 2000-01-01` | Age calculator |
| `/bmi 180 75` | BMI from cm/kg |

### Profile automation

| Command | Description |
| --- | --- |
| `/bio set <text>` / `/bio list` / `/bio add <text>` / `/bio remove <id>` | Manage bios / random rotation |
| `/bio random` | Set a random bio |
| `/bio clock on/off` | Bio with current time |
| `/bio online on/off` | Bio based on online status |
| `/autobio on/off` | Rotate bios automatically |
| `/biotime add 09:00-13:00 "Working"` / `/biotime list` / `/biotime remove <id>` | Time-based bios |
| `/username` / `/username 10` | Generate usernames (change requires confirmation) |
| `/profilephoto generate` / `/profilephoto set <file>` | Generate or set a profile photo |
| `/profile backup` | Backup name/bio/username/photo |
| `/profile restore <backup_id>` | Restore a backup (confirmation required) |

## Development

```powershell
# Run the tests (143 tests)
pytest -q

# Lint
ruff check src tests scripts

# Type check
mypy src/selfbot --ignore-missing-imports

# Offline smoke test: registers every command without connecting to Telegram
python scripts/_smoke_test.py
```

### Project layout

```
src/selfbot/
├── app.py                    # bootstrap & lifecycle
├── config.py                 # pydantic Settings (.env)
├── services_container.py     # service wiring (dependency injection)
├── database/                 # SQLAlchemy async models, engine, repositories
├── services/                 # business logic: reminders, autoreply, ai, network, ...
├── telegram/
│   ├── client.py             # Telethon client setup + auth
│   ├── dispatcher.py         # command registry, context, permissions hookup
│   ├── confirmation.py       # confirmation manager for destructive actions
│   └── handlers/             # thin Telegram command handlers (persian UX)
├── utils/                    # ssrf, rate_limit, validators, logging
└── messages/persian.py       # user-facing Persian strings
```

## Security notes

- SSRF protection blocks loopback/private/link-local/carrier-grade NAT and cloud-metadata destinations for all network tools.
- The calculator parses expressions safely and never uses `eval()`.
- Passwords, JWTs, API keys, session strings are never logged; logging is structured and redacted.
- Destructive and profile-modifying actions require Persian confirmation (`بله`/`خیر`) by default.
- Download size, timeout, and rate limits are enforced.

## License

MIT License