import os
import json
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ Welcome to Phishing Link Detector Bot!\n\n"
        "Send any URL and I will analyze it.\n"
        "Example: https://example.com"
    )

async def check_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("⚠️ Please send a valid URL starting with https://")
        return

    await update.message.reply_text("🔍 Scanning in progress...")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Analyze whether this URL is a phishing link and reply with JSON only:
URL: {url}

{{
  "verdict": "safe/suspicious/dangerous",
  "risk_score": 0-100,
  "summary": "2 sentences in English",
  "flags": ["issue1", "issue2"]
}}"""
            }]
        )

        text = response.content[0].text
        clean = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)

        if data["verdict"] == "safe":
            icon, label = "✅", "Safe"
        elif data["verdict"] == "suspicious":
            icon, label = "⚠️", "Suspicious"
        else:
            icon, label = "🚨", "Dangerous"

        flags_text = "\n".join([f"• {f}" for f in data.get("flags", [])]) or "No issues found"

        reply = (
            f"{icon} *Result: {label}*\n\n"
            f"🎯 Risk Score: `{data['risk_score']}/100`\n\n"
            f"📋 Analysis:\n{data['summary']}\n\n"
            f"🔴 Issues Found:\n{flags_text}"
        )

        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text("❌ Analysis failed. Please try again.")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_url))
app.run_polling()