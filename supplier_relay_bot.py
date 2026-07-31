import os
import logging
from typing import Dict

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPLIER_CHAT_ID = int(os.getenv("SUPPLIER_CHAT_ID", "0"))

# Comma-separated Telegram numeric user IDs, e.g. "111111111,222222222"
TEAM_USER_IDS = {
    int(user_id.strip())
    for user_id in os.getenv("TEAM_USER_IDS", "").split(",")
    if user_id.strip()
}

# Maps the message sent to the supplier -> the team member who sent it.
# This is kept in memory. For production, replace it with SQLite or PostgreSQL.
message_routes: Dict[int, int] = {}


def is_team_member(user_id: int) -> bool:
    return user_id in TEAM_USER_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    await update.message.reply_text(
        f"Your Telegram user ID is: {user.id}\n"
        f"This chat ID is: {chat.id}\n\n"
        "Send these numbers to the bot owner for setup."
    )


async def relay_team_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    if not is_team_member(user.id):
        await message.reply_text("You are not authorized to use this bot.")
        return

    # The supplier only sees a generic team reference, not the member's username.
    header = f"📩 New team request\nReference: TEAM-{user.id}\n\n"

    if message.text:
        sent = await context.bot.send_message(
            chat_id=SUPPLIER_CHAT_ID,
            text=header + message.text,
        )
    else:
        # Copying avoids showing the original sender identity.
        sent = await context.bot.send_message(
            chat_id=SUPPLIER_CHAT_ID,
            text=header + "Attachment received below:",
        )
        copied = await context.bot.copy_message(
            chat_id=SUPPLIER_CHAT_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id,
        )
        message_routes[copied.message_id] = user.id

    message_routes[sent.message_id] = user.id
    await message.reply_text("✅ Sent to the supplier.")


async def relay_supplier_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.effective_message
    chat = update.effective_chat

    if not message or not chat or chat.id != SUPPLIER_CHAT_ID:
        return

    if not message.reply_to_message:
        await message.reply_text(
            "Please reply directly to the team request you want to answer."
        )
        return

    original_message_id = message.reply_to_message.message_id
    team_user_id = message_routes.get(original_message_id)

    if not team_user_id:
        await message.reply_text(
            "I cannot find the original team member. "
            "The bot may have restarted, or this message was not routed by the bot."
        )
        return

    if message.text:
        await context.bot.send_message(
            chat_id=team_user_id,
            text="📦 Supplier reply:\n\n" + message.text,
        )
    else:
        await context.bot.send_message(
            chat_id=team_user_id,
            text="📦 Supplier sent an attachment:",
        )
        await context.bot.copy_message(
            chat_id=team_user_id,
            from_chat_id=SUPPLIER_CHAT_ID,
            message_id=message.message_id,
        )

    await message.reply_text("✅ Reply delivered to the team member.")


async def route_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    if chat.id == SUPPLIER_CHAT_ID:
        await relay_supplier_reply(update, context)
    else:
        await relay_team_message(update, context)


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing.")
    if not SUPPLIER_CHAT_ID:
        raise RuntimeError("SUPPLIER_CHAT_ID is missing.")
    if not TEAM_USER_IDS:
        raise RuntimeError("TEAM_USER_IDS is missing.")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, route_message)
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
