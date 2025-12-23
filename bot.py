import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# ---------- ЛОГІКА ДЕФІЦИТІВ ----------

DEFICIENCIES = ["Азот (N)", "Фосфор (P)", "Калій (K)", "Магній (Mg)"]

QUESTIONS = [
    {
        "text": "Чи листя світло-зелене або жовтіє знизу?",
        "weights": {"Азот (N)": 2, "Магній (Mg)": 1},
    },
    {
        "text": "Чи рослини відстають у рості?",
        "weights": {"Азот (N)": 1, "Фосфор (P)": 2},
    },
    {
        "text": "Чи краї листків підсихають або буріють?",
        "weights": {"Калій (K)": 2},
    },
    {
        "text": "Чи є пожовтіння між жилками листка?",
        "weights": {"Магній (Mg)": 2},
    },
]

# ---------- TELEGRAM ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌱 Бот діагностики дефіцитів картоплі\n\n"
        "Команди:\n"
        "/diagnose — почати діагностику"
    )

async def diagnose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["step"] = 0
    context.user_data["scores"] = {d: 0 for d in DEFICIENCIES}
    await update.message.reply_text(QUESTIONS[0]["text"])

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "step" not in context.user_data:
        return

    step = context.user_data["step"]
    answer = update.message.text.lower()

    if answer == "так":
        for d, w in QUESTIONS[step]["weights"].items():
            context.user_data["scores"][d] += w

    step += 1
    context.user_data["step"] = step

    if step >= len(QUESTIONS):
        scores = context.user_data["scores"]
        result = max(scores, key=scores.get)

        text = "📊 Результат:\n\n"
        for d, s in scores.items():
            text += f"{d}: {s}\n"
        text += f"\n✅ Найімовірніший дефіцит: {result}"

        await update.message.reply_text(text)
        context.user_data.clear()
    else:
        await update.message.reply_text(QUESTIONS[step]["text"])

# ---------- FLASK + WEBHOOK ----------

app = Flask(__name__)
telegram_app: Application = ApplicationBuilder().token(TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("diagnose", diagnose))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))


#@app.route("/", methods=["POST"])
#async def webhook():
#    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
#    await telegram_app.process_update(update)
#    return "ok" 

@app.route("/", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    print("INCOMING UPDATE:", data)

    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def health():
    return "Bot is running"

# ---------- MAIN ----------

@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    telegram_app.bot.set_webhook(WEBHOOK_URL)
    return "Webhook set"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
