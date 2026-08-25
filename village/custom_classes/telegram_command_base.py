from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


class TelegramCommandBase:
    """Base class for a custom Telegram bot command.

    Subclass in the project code directory so it is picked up by import_all.
    Set command to the slash-command name (no slash) and implement
    handler. Args after the command arrive in context.args as strings.
    Wrap risky work in try/except so one bad command can't kill the bot.
    Set description to a short one-line explanation shown by /help.
    """

    command = ""  # e.g. "do_stuff" -> /do_stuff
    description = ""  # shown next to the command in /help

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Respond to the command."""
        raise NotImplementedError
