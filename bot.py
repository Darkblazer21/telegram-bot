import asyncio
import logging
import os
import smtplib
from email.mime.text import MIMEText
from datetime import timedelta

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BASE_URL = "https://api.frankfurter.app"

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.environ.get("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT") or EMAIL_ADDRESS


def _fetch_rate() -> float:
    r = requests.get(f"{BASE_URL}/latest?from=USD&to=EUR", timeout=10)
    r.raise_for_status()
    return r.json()["rates"]["EUR"]


async def get_rate() -> float:
    return await asyncio.to_thread(_fetch_rate)


def _send_email_sync(subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_RECIPIENT
    with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


async def send_email(subject: str, body: str) -> None:
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
        logging.warning("Email not configured. Set EMAIL_ADDRESS, EMAIL_PASSWORD, and EMAIL_RECIPIENT.")
        return
    await asyncio.to_thread(_send_email_sync, subject, body)


async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        rate = await get_rate()
        await update.message.reply_text(f"USD = {rate} EUR")
    except requests.RequestException:
        await update.message.reply_text("Failed to fetch exchange rate.")


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /alert <threshold>\nExample: /alert 0.90")
        return

    try:
        threshold = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Threshold must be a number (e.g., 0.90).")
        return

    context.bot_data.setdefault("thresholds", {})
    context.bot_data["thresholds"][update.effective_user.id] = threshold
    await update.message.reply_text(
        f"Alert set! You'll be notified when USD/EUR exceeds {threshold}."
    )


async def check_rates(context: ContextTypes.DEFAULT_TYPE) -> None:
    thresholds = context.bot_data.get("thresholds", {})
    if not thresholds:
        return

    try:
        rate = await get_rate()
    except requests.RequestException:
        logging.error("Failed to fetch rate in scheduled check.")
        return

    triggered = [uid for uid, t in thresholds.items() if rate > t]

    if triggered:
        await send_email(
            "Exchange Rate Alert",
            f"USD/EUR rate is {rate}, exceeding the threshold(s) you set.",
        )

        for uid in triggered:
            del context.bot_data["thresholds"][uid]


def main() -> None:
    app = ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()

    app.add_handler(CommandHandler("rate", rate_command))
    app.add_handler(CommandHandler("alert", alert_command))

    app.job_queue.run_repeating(
        check_rates, interval=timedelta(hours=12), first=timedelta(hours=12)
    )

    app.run_polling()


if __name__ == "__main__":
    main()
