# AGENTS.md

## Project

Single-file Telegram bot (`bot.py`) for USD/EUR/XOF exchange rate monitoring using the Frankfurter API.

## Commands

- **Run**: `python bot.py`
- **Dependencies**: `pip install "python-telegram-bot[job-queue]" requests python-dotenv`

No tests, no CI, no lint/typecheck config.

## Setup

- `.env` file required with `TELEGRAM_BOT_TOKEN`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `EMAIL_RECIPIENT`
- Gmail requires an **App Password** (not regular password) when 2FA is enabled
- `.env` and `__pycache__/` are gitignored

## API

- Frankfurter API: `https://api.frankfurter.app/latest?from=USD&to=EUR` (**not** `.dev`)
- XOF rate is constant: `655.957` (peg to EUR), calculated as `eur_rate * 655.957`

## Architecture

- Commands: `/rate`, `/amount`, `/alert`, `/urgent`
- Thresholds stored in `context.bot_data["thresholds"]` (in-memory, lost on restart)
- Periodic check every 12 hours via `job_queue`
- Email via `smtplib` with STARTTLS (defaults to Gmail SMTP on port 587)

## Gotchas

- `python-telegram-bot` must be installed with `[job-queue]` extra or `app.job_queue` is `None`
- All blocking I/O (HTTP requests, SMTP) routed through `asyncio.to_thread` to avoid blocking the event loop
- Frankfurter API returns 404 for XOF directly — XOF is derived from EUR rate
- Email errors surface as unhandled exceptions (no error handler registered on the Application)
