import os
import yaml
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# НАЛАШТУВАННЯ
# =========================
TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = "https://potatobot-18ot.onrender.com/webhook"
PORT = 10000

# =========================
# ЗАВАНТАЖЕННЯ ПРАВИЛ
# =========================
with open("rules.yaml", "r", encoding="utf-8") as f:
    RULES = yaml.safe_load(f)

SYMPTOMS = list(RULES["symptoms"].keys())

# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["step"] = 0
    context.user_data["answers"] = []

    await update.message.reply_text(
        "🌱 Визначення дефіциту живлення картоплі\n"
        "Відповідай на запитання «Так» або «Ні»."
    )

    await ask_question(update, context)

# =========================
# ЗАДАТИ ПИТАННЯ
# =========================
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data["step"]

    if step >= len(SYMPTOMS):
        await show_result(update, context)
        return

    symptom_key = SYMPTOMS[step]
    question = RULES["symptoms"][symptom_key]["question"]

    keyboard = ReplyKeyboardMarkup(
        [["Так", "Ні"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(question, reply_markup=keyboard)

# =========================
# ОБРОБКА ВІДПОВІДІ
# =========================
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text not in ["Так", "Ні"]:
        return

    step = context.user_data["step"]

    if text == "Так":
        context.user_data["answers"].append(SYMPTOMS[step])

    context.user_data["step"] += 1
    await ask_question(update, context)

# =========================
# РЕЗУЛЬТАТ
# =========================
async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answers = context.user_data["answers"]
    scores = {}

    for key, data in RULES["rules"]["nutrition"].items():
        score = 0
        for symptom, weight in data["weights"].items():
            if symptom in answers:
                score += weight

        if score > 0:
            scores[data["name"]] = score

    if not scores:
        await update.message.reply_text(
            "✅ Ознак явного дефіциту живлення не виявлено.\n"
            "Рекомендується додатковий огляд поля."
        )
        return

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    text = "🌱 *Ймовірні дефіцити живлення:*\n\n"
    for name, score in sorted_scores:
        text += f"🔸 {name} — {score} балів\n"

    text += (
        "\nℹ️ Це експертна оцінка на основі симптомів.\n"
        "Рекомендується підтвердження аналізом або оглядом."
    )

    await update.message.reply_text(text, parse_mode="Markdown")

# =========================
# ЗАПУСК
# =========================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
