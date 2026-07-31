# Private Supplier Relay Bot

## What it does
- Team members message the bot.
- The bot sends their requests to the supplier.
- The team never sees the supplier's Telegram profile.
- The supplier replies directly to the relayed message.
- The bot sends the reply back to the correct team member.

## Setup
1. Open Telegram and message @BotFather.
2. Run `/newbot`, create the bot, and copy the token.
3. Install Python 3.10 or newer.
4. Open a terminal in this folder.
5. Run:
   `pip install -r requirements.txt`
6. Rename `.env.example` to `.env`.
7. Put the token in `.env`.
8. Temporarily run the bot and ask every team member and the supplier to send `/start`.
9. Copy their numeric IDs into `.env`.
10. Start the bot with:
    `python supplier_relay_bot.py`

## Important
The basic version stores message routing in memory. If the program restarts,
old supplier replies may no longer be routed. Use a database for a production version.
