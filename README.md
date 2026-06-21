# telegram-bot

A Telegram bot for real-time exchange rate monitoring between **USD**, **EUR**, and **XOF** (CFA Franc). Uses the [Frankfurter API](https://www.frankfurter.app/) (free, no key required) and supports email alerts via SMTP when a threshold is breached.

## Features

- **`/rate`** – Display the current USD → EUR and USD → XOF exchange rates.
- **`/amount <amount> <currency>`** – Convert an amount from **dollar** (or `usd`) / **euro** (or `eur`) to the other two currencies. Output uses space as thousands separator.
- **`/alert <threshold>`** – Set a threshold on the USD/EUR rate. When the rate exceeds it, an email alert is sent. The bot checks every 12 hours automatically.
- **`/urgent <threshold>`** – One-shot threshold check. Fetches the rate immediately and sends an email if exceeded. Useful for testing email configuration.

## Requirements

- Python 3.9+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords) (or any SMTP server)

## Setup

1. **Clone the repo and install dependencies**

   ```bash
   pip install "python-telegram-bot[job-queue]" requests python-dotenv
   ```

2. **Create a `.env` file** in the project root:

   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   EMAIL_ADDRESS=your.email@gmail.com
   EMAIL_PASSWORD=your_app_password_here
   EMAIL_RECIPIENT=your.email@gmail.com
   ```

   Optional SMTP overrides (defaults to Gmail):
   ```
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   ```

3. **Run the bot**

   ```bash
   python bot.py
   ```

## Usage

| Command | Example | Description |
|---|---|---|
| `/rate` | `/rate` | Shows USD = 0.87 EUR = 570.23 XOF |
| `/amount` | `/amount 20 dollar` | Converts 20 USD → EUR and XOF |
| `/amount` | `/amount 50 euro` | Converts 50 EUR → USD and XOF |
| `/alert` | `/alert 0.90` | Alert me by email when USD/EUR exceeds 0.90 |
| `/urgent` | `/urgent 0.80` | Check now and send email immediately if exceeded |

## Notes

- XOF is pegged to EUR at `655.957`. The bot calculates USD → XOF as `(USD→EUR) × 655.957`.
- Thresholds are reset after triggering (one-time alert per threshold).
- The periodic check runs every 12 hours.
