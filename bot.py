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


XOF_RATE = 655.957


def _fetch_rates() -> tuple[float, float]:
    r = requests.get(f"{BASE_URL}/latest?from=USD&to=EUR", timeout=10)
    r.raise_for_status()
    eur = r.json()["rates"]["EUR"]
    xof = round(eur * XOF_RATE, 2)
    return eur, xof


async def get_rates() -> tuple[float, float]:
    return await asyncio.to_thread(_fetch_rates)


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


def format_number(n: float) -> str:
    return format(n, ",.2f").replace(",", " ")


async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        eur, xof = await get_rates()
        await update.message.reply_text(f"USD = {eur} EUR = {xof} XOF")
    except requests.RequestException:
        await update.message.reply_text("Failed to fetch exchange rate.")


async def amount_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /amount <amount> <currency>\nExample: /amount 20 dollar")
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Amount must be a number.")
        return

    currency = context.args[1].lower()
    if currency in ("dollar", "dollars", "usd"):
        from_usd = True
    elif currency in ("euro", "euros", "eur"):
        from_usd = False
    else:
        await update.message.reply_text('Currency must be "dollar" or "euro".')
        return

    try:
        usd_to_eur, _ = await get_rates()
    except requests.RequestException:
        await update.message.reply_text("Failed to fetch exchange rate.")
        return

    if from_usd:
        eur = round(amount * usd_to_eur, 2)
        xof = round(eur * XOF_RATE, 2)
        await update.message.reply_text(
            f"{format_number(eur)} EUR = {format_number(xof)} XOF"
        )
    else:
        usd = round(amount / usd_to_eur, 2)
        xof = round(amount * XOF_RATE, 2)
        await update.message.reply_text(
            f"{format_number(usd)} USD = {format_number(xof)} XOF"
        )


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


async def urgent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /urgent <threshold>\nExample: /urgent 0.80")
        return

    try:
        threshold = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Threshold must be a number (e.g., 0.80).")
        return

    await update.message.reply_text("Fetching rate and checking...")

    try:
        rate, _ = await get_rates()
    except requests.RequestException:
        await update.message.reply_text("Failed to fetch exchange rate.")
        return

    if rate > threshold:
        await send_email(
            "Urgent Exchange Rate Alert",
            f"USD/EUR rate is {rate}, exceeding your threshold of {threshold}.",
        )
        await update.message.reply_text(
            f"Rate {rate} exceeds {threshold}. Alert email sent to {EMAIL_RECIPIENT}."
        )
    else:
        await update.message.reply_text(
            f"Rate {rate} does not exceed {threshold}. No email sent."
        )


async def check_rates(context: ContextTypes.DEFAULT_TYPE) -> None:
    thresholds = context.bot_data.get("thresholds", {})
    if not thresholds:
        return

    try:
        rate, _ = await get_rates()
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
    app.add_handler(CommandHandler("urgent", urgent_command))
    app.add_handler(CommandHandler("amount", amount_command))

    app.job_queue.run_repeating(
        check_rates, interval=timedelta(hours=12), first=timedelta(hours=12)
    )

    app.run_polling()


if __name__ == "__main__":
    main()
