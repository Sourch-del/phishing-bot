import os
import json
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

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
        prompt = f"""Analyze whether this URL is a phishing link and reply with JSON only, no markdown:
URL: {url}

{{
  "verdict": "safe or suspicious or dangerous",
  "risk_score": 0-100,
  "summary": "2 sentences in English",
  "flags": ["issue1", "issue2"]
}}"""

        response = model.generate_content(prompt)
        clean = response.text.replace("```json", "").replace("```", "").strip()
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