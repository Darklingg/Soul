import json
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = "YOUR_BOT_TOKEN_HERE"

ASK_COUNTRY_RESULTS = 1
ASK_COUNTRY_MATCHES = 2

DATA_FILE = Path(__file__).with_name("matches.json")


def load_matches():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Не найден файл {DATA_FILE.name}. "
            "Создай его рядом с файлом бота."
        )

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("matches.json должен содержать JSON-массив матчей.")

    required_fields = {"home", "away", "home_score", "away_score"}

    for index, match in enumerate(data, start=1):
        if not isinstance(match, dict):
            raise ValueError(f"Матч №{index} должен быть объектом.")

        missing = required_fields - match.keys()
        if missing:
            raise ValueError(
                f"В матче №{index} отсутствуют поля: {', '.join(sorted(missing))}"
            )

    return data


MATCHES = load_matches()


def get_countries():
    countries = set()

    for match in MATCHES:
        countries.add(str(match["home"]))
        countries.add(str(match["away"]))

    return sorted(countries)


def format_result(match):
    return (
        f"{match['home']} {match['home_score']} - "
        f"{match['away_score']} {match['away']}"
    )


def format_match(match):
    return (
        f"{match['home']} vs {match['away']} "
        f"({match['home_score']}-{match['away_score']})"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    countries = ", ".join(get_countries())

    text = (
        "FIFA Tournament Bot\n\n"
        "Команды:\n"
        "/results — результаты матчей страны или всех стран\n"
        "/matches — матчи страны или всех стран\n"
        "/countries — список стран\n"
        "/cancel — отменить текущую операцию\n\n"
        f"Страны: {countries}"
    )

    await update.message.reply_text(text)


async def countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Страны:\n" + "\n".join(get_countries())
    )


async def results_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Напиши название страны или 'all' для всех результатов."
    )
    return ASK_COUNTRY_RESULTS


async def results_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text.strip()

    if country.lower() == "all":
        lines = ["Все результаты:"]

        for match in MATCHES:
            lines.append(format_result(match))

        await update.message.reply_text("\n".join(lines))
        await update.message.reply_text(
            "Напиши другую страну, 'all' или /cancel."
        )
        return ASK_COUNTRY_RESULTS

    results = [
        match for match in MATCHES
        if str(match["home"]).lower() == country.lower()
        or str(match["away"]).lower() == country.lower()
    ]

    if not results:
        await update.message.reply_text(
            "Страна не найдена. Попробуй ещё раз или используй /cancel."
        )
        return ASK_COUNTRY_RESULTS

    lines = [f"Результаты для {country}:"]

    for match in results:
        lines.append(format_result(match))

    await update.message.reply_text("\n".join(lines))
    await update.message.reply_text(
        "Напиши другую страну, 'all' или /cancel."
    )
    return ASK_COUNTRY_RESULTS


async def matches_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Напиши название страны или 'all' для всех матчей."
    )
    return ASK_COUNTRY_MATCHES


async def matches_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text.strip()

    if country.lower() == "all":
        lines = ["Все матчи:"]

        for match in MATCHES:
            lines.append(format_match(match))

        await update.message.reply_text("\n".join(lines))
        await update.message.reply_text(
            "Напиши другую страну, 'all' или /cancel."
        )
        return ASK_COUNTRY_MATCHES

    matches = [
        match for match in MATCHES
        if str(match["home"]).lower() == country.lower()
        or str(match["away"]).lower() == country.lower()
    ]

    if not matches:
        await update.message.reply_text(
            "Страна не найдена. Попробуй ещё раз или используй /cancel."
        )
        return ASK_COUNTRY_MATCHES

    lines = [f"Матчи для {country}:"]

    for match in matches:
        lines.append(format_match(match))

    await update.message.reply_text("\n".join(lines))
    await update.message.reply_text(
        "Напиши другую страну, 'all' или /cancel."
    )
    return ASK_COUNTRY_MATCHES


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


def main():
    if TOKEN == "YOUR_BOT_TOKEN_HERE" or not TOKEN.strip():
        raise ValueError(
            "Вставь токен бота в переменную TOKEN в начале файла."
        )

    app = Application.builder().token(TOKEN).build()

    results_conv = ConversationHandler(
        entry_points=[CommandHandler("results", results_command)],
        states={
            ASK_COUNTRY_RESULTS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    results_response,
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    matches_conv = ConversationHandler(
        entry_points=[CommandHandler("matches", matches_command)],
        states={
            ASK_COUNTRY_MATCHES: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    matches_response,
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("countries", countries))
    app.add_handler(results_conv)
    app.add_handler(matches_conv)

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()