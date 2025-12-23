import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = os.getenv("TOKEN")

# ===== ДЕФІЦИТИ =====
ELEMENTS = ["N", "K", "Mg", "P", "Ca"]

# ===== СИМПТОМИ =====
SYMPTOMS = [
    ("S1", "Жовтіє нижнє листя?"),
    ("S2", "Жовтіє верхнє листя?"),
    ("S3", "Є некроз країв листка?"),
    ("S4", "Листя має фіолетовий відтінок?"),
    ("S5", "Жовтіння між жилками?"),
    ("S6", "Листя скручується вгору?"),
    ("S7", "Відмирають точки росту?"),
    ("S8", "Симптоми посилюються в посуху?"),
    ("S9", "Листя ламке або крихке?"),
    ("S10", "Рослини відстають у рості?")
]

# ===== ТАБЛИЦЯ ВАГ =====
WEIGHTS = {
    "S1": {"N": 3, "K": 0, "Mg": 2, "P": 1, "Ca": -1},
    "S2": {"N": -2, "K": 0, "Mg": -1, "P": -1, "Ca": 3},
    "S3": {"N": 0, "K": 3, "Mg": -1, "P": 0, "Ca": 1},
    "S4": {"N": -1, "K": 0, "Mg": 0, "P": 4, "Ca": -1},
    "S5": {"N": -1, "K": 0, "Mg": 4, "P": 0, "Ca": -1},
    "S6": {"N": 0, "K": 3, "Mg": 0, "P": 0, "Ca": 1},
    "S7": {"N": 0, "K": 0, "Mg": -1, "P": 0, "Ca": 4},
    "S8": {"N": 0, "K": 3, "Mg": 1, "P": 0, "Ca": 2},
    "S9": {"N": -1, "K": 0, "Mg": 0, "P": 0, "Ca": 3},
    "S10":{"N": 3, "K": 1, "Mg": 1, "P": 2, "Ca": 1}
}

# ===== СТАРТ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["step"] = 0
    context.user_data["scores"] = {el: 0 for el in ELEMENTS}
    await ask_question(update, context)

# ===== ПИТАННЯ =====
async def ask_question(update, context):
    step = context.user_data["step"]

    if step >= len(SYMPTOMS):
        await show_result(update, context)
        return

    code, text = SYMPTOMS[step]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Так", callback_data=f"{code}:yes"),
            InlineKeyboardButton("❌ Ні", callback_data=f"{code}:no"),
            InlineKeyboardButton("❓ Не знаю", callback_data=f"{code}:skip")
        ]
    ])

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard)
    else:
        await update.callback_query.message.reply_text(text, reply_markup=keyboard)

# ===== ОБРОБКА КНОПОК =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    code, answer = query.data.split(":")
    scores = context.user_data["scores"]

    if answer != "skip":
        for el, w in WEIGHTS[code].items():
            if answer == "yes":
                scores[el] += w
            elif answer == "no":
                scores[el] -= w * 0.5

    context.user_data["step"] += 1
    await query.message.delete()
    await ask_question(update, context)

# ===== РЕЗУЛЬТАТ =====
async def show_result(update, context):
    scores = context.user_data["scores"]
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    max_score = max(v for _, v in sorted_scores) or 1

    text = "🌱 *Ймовірні дефіцити живлення картоплі:*\n\n"
    for el, val in sorted_scores:
        percent = round((val / max_score) * 100)
        text += f"• *{el}* — {percent}%\n"

    text += "\nℹ️ Результат є орієнтовним і не замінює польову діагностику."

    await update.callback_query.message.reply_text(
        text,
        parse_mode="Markdown"
    )

# ===== ЗАПУСК =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    PORT = int(os.environ.get("PORT", 8443))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://YOUR-APP.onrender.com/{TOKEN}"
    )

if __name__ == "__main__":
    main()
