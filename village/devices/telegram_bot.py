import asyncio
import json
import os
import threading
import time
import traceback
from urllib import parse, request

import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from village.classes.null_classes import NullTelegramBot
from village.devices.camera import cam_box, cam_corridor
from village.manager import manager
from village.plots.corridor_plot import corridor_plot
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.settings import settings


class TelegramBot:
    """A Telegram Bot for controlling and monitoring the village system.

    Attributes:
        token (str): The Telegram bot token.
        chat (str): The chat ID to send alarms to.
        message (str): Current message buffer.
        connected (bool): Connection status.
        error_running (bool): Flag indicating if an error occurred during the loop.
        error (str): Error message.
        thread (threading.Thread): Background thread for the bot loop.
        application (Application): The python-telegram-bot application instance.
    """

    def __init__(self) -> None:
        """Initializes the TelegramBot and starts the background loop."""
        self.token = settings.get("TELEGRAM_TOKEN")
        self.chat = settings.get("TELEGRAM_CHAT")
        self.message = ""
        self.connected = False
        self.error_running = False
        self.error = ""
        self.pending: dict[int, str] = {}
        self.alarm_id = 0

        self.thread = threading.Thread(target=self.botloop, daemon=True)
        self.thread.start()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Responds to the /start command.

        Args:
            update (Update): The update object.
            context (ContextTypes.DEFAULT_TYPE): The context object.
        """
        text = "Hi! Use /report <hours> to get a report of the last hours."
        await update.message.reply_text(text)

    def alarm(self, message: str, repeat: bool = False) -> None:
        """Sends an alarm message to the configured chat.

        Repeatable alarms are kept in self.pending and resent every
        TELEGRAM_REPEAT_MINUTES until acknowledged, either with the button in
        telegram or with the ALARM button in the GUI.

        Args:
            message (str): The message content.
            repeat (bool): True to resend the alarm until it is acknowledged.
        """
        if repeat:
            first_line = message.split("\n")[0]
            self.pending = {
                k: v for k, v in self.pending.items() if v.split("\n")[0] != first_line
            }
            self.alarm_id += 1
            self.pending[self.alarm_id] = message
            self.send(message, self.alarm_id)
        else:
            self.send(message, None)

    def send(self, message: str, ack_id: int | None) -> None:
        """Sends a message, optionally with an acknowledge button.

        Uses plain http because it is called from threads outside the bot
        asyncio loop.

        Args:
            message (str): The message content.
            ack_id (int | None): Id of the alarm to acknowledge, if any.
        """
        try:
            url = "https://api.telegram.org/bot%s/sendMessage" % self.token
            values = {"chat_id": self.chat, "text": message}
            if ack_id is not None:
                values["reply_markup"] = json.dumps(
                    {
                        "inline_keyboard": [
                            [
                                {
                                    "text": "✅ Acknowledge",
                                    "callback_data": "ack:%d" % ack_id,
                                }
                            ]
                        ]
                    }
                )
            data = parse.urlencode(values)
            request.urlopen(url, data.encode("utf-8"), timeout=10)
        except Exception:
            log.error("Telegram error sending alarm", exception=traceback.format_exc())

    async def ack(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Acknowledges an alarm from the button in Telegram.

        Args:
            update (Update): The update object.
            context (ContextTypes.DEFAULT_TYPE): The context object.
        """
        query = update.callback_query
        try:
            await query.answer()
            self.pending.pop(int(query.data.split(":")[1]), None)
            await query.edit_message_text(
                query.message.text + "\n\n✅ Acknowledged by " + query.from_user.name
            )
        except Exception:
            log.error("Telegram error acknowledging", exception=traceback.format_exc())

    async def repeat_alarms(self) -> None:
        """Resends unacknowledged alarms until they are acknowledged."""
        while True:
            minutes = settings.get("TELEGRAM_REPEAT_MINUTES") or 30
            await asyncio.sleep(60 * minutes)
            for ack_id, message in list(self.pending.items()):
                self.send(message, ack_id)

    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generates and sends a report for the specified number of hours.

        Args:
            update (Update): The update object.
            context (ContextTypes.DEFAULT_TYPE): The context object (contains args).
        """
        try:
            hours = int(context.args[0])
            if hours < 1:
                hours = 24
            elif hours > 240:  # 10 days max
                hours = 240
        except (ValueError, IndexError, TypeError):
            hours = 24

        try:
            report, _, _, _, _ = manager.create_report(hours)
            await update.message.reply_text(report)
        except Exception:
            log.error(
                "Telegram error creating report", exception=traceback.format_exc()
            )

    async def cam(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Takes pictures from cameras and sends them.

        Args:
            update (Update): The update object.
            context (ContextTypes.DEFAULT_TYPE): The context object.
        """
        try:
            cam_corridor.take_picture()
            cam_box.take_picture()
            await asyncio.sleep(1)
            with open(cam_corridor.path_picture, "rb") as picture_corridor:
                await update.message.reply_photo(photo=picture_corridor)
            with open(cam_box.path_picture, "rb") as picture_box:
                await update.message.reply_photo(photo=picture_box)
            if os.path.exists(cam_corridor.path_picture):
                os.remove(cam_corridor.path_picture)
            if os.path.exists(cam_box.path_picture):
                os.remove(cam_box.path_picture)
        except Exception:
            log.error("Telegram error sending photos", exception=traceback.format_exc())

    async def plot(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generates and sends a plot of corridor events.

        Args:
            update (Update): The update object.
            context (ContextTypes.DEFAULT_TYPE): The context object.
        """
        try:
            path = os.path.join(settings.get("SYSTEM_DIRECTORY"), "PLOT.jpg")
            subjects_df = manager.subjects.df
            subjects = subjects_df["name"].tolist()
            active_states = dict(zip(subjects_df["name"], subjects_df["active"]))
            fig = corridor_plot(
                manager.events.df.copy(), subjects, 4, 2, active_states=active_states
            )
            fig.savefig(path, format="jpg", dpi=300)
            plt.close(fig)
            await asyncio.sleep(1)
            with open(path, "rb") as picture:
                await update.message.reply_photo(photo=picture)
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            log.error("Telegram error sending plot", exception=traceback.format_exc())

    async def main(self) -> None:
        """Main asyncio loop for the bot application."""
        self.application = ApplicationBuilder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.start))
        self.application.add_handler(CommandHandler("report", self.report))
        self.application.add_handler(CommandHandler("plot", self.plot))
        self.application.add_handler(CommandHandler("cam", self.cam))
        self.application.add_handler(CallbackQueryHandler(self.ack))

        try:
            await self.application.initialize()
            await self.application.updater.start_polling()
            await self.application.start()
        except TypeError:
            pass
        self.connected = True
        await self.repeat_alarms()

    async def botloop_starttask(self) -> None:
        """Starts the main bot task."""
        bot_routine = asyncio.create_task(self.main())
        await bot_routine

    def botloop(self) -> None:
        """Entry point for the bot thread."""
        try:
            asyncio.run(self.botloop_starttask())
        except Exception:
            self.error_running = True
            self.error = log.clean_text(traceback.format_exc(), "Telegram error")


def get_telegram_bot() -> TelegramBot | NullTelegramBot:
    """Factory function to initialize and connect the TelegramBot.

    Returns:
        TelegramBotBase: An initialized TelegramBot instance or base class on failure.
    """
    if not manager.use_of_corridor:
        null_telegram_bot = NullTelegramBot()
        null_telegram_bot.error = ""
        return null_telegram_bot
    try:
        telegram_bot = TelegramBot()
        chrono = time_utils.Chrono()
        while (
            not telegram_bot.connected
            and not telegram_bot.error_running
            and chrono.get_seconds() < 30
        ):
            time.sleep(0.1)
        if telegram_bot.connected:
            return telegram_bot
        elif telegram_bot.error_running:
            null_telegram_bot = NullTelegramBot()
            null_telegram_bot.error = telegram_bot.error
            return null_telegram_bot
        else:
            null_telegram_bot = NullTelegramBot()
            null_telegram_bot.error = "Could not initialize telegram bot, time expired"
            return null_telegram_bot
    except Exception:
        null_telegram_bot = NullTelegramBot()
        null_telegram_bot.error = log.clean_text(
            traceback.format_exc(), "Could not initialize telegram bot"
        )
        return null_telegram_bot


telegram_bot = get_telegram_bot()
