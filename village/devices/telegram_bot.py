import asyncio
import os
import threading
import time
import traceback
from urllib import parse, request

import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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

    def alarm(self, message: str) -> None:
        """Sends an alarm message to the configured chat.

        Args:
            message (str): The message content.
        """
        try:
            url = "https://api.telegram.org/bot%s/sendMessage" % self.token
            data = parse.urlencode({"chat_id": self.chat, "text": message})
            request.urlopen(url, data.encode("utf-8"))
        except Exception:
            log.error("Telegram error sending alarm", exception=traceback.format_exc())

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
            subjects = manager.subjects.df["name"].tolist()
            fig = corridor_plot(manager.events.df.copy(), subjects, 4, 2)
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

        try:
            await self.application.initialize()
            await self.application.updater.start_polling()
            await self.application.start()
        except TypeError:
            pass
        self.connected = True
        while True:
            await asyncio.sleep(1)

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
            log.error("Telegram error", exception=traceback.format_exc())


def get_telegram_bot() -> TelegramBot | NullTelegramBot:
    """Factory function to initialize and connect the TelegramBot.

    Returns:
        TelegramBotBase: An initialized TelegramBot instance or base class on failure.
    """
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
            log.info("Telegram bot successfully initialized")
            return telegram_bot
        elif telegram_bot.error_running:
            return NullTelegramBot()
        else:
            log.error("Could not initialize telegram bot, time expired")
            return NullTelegramBot()
    except Exception:
        log.error("Could not initialize telegram bot", exception=traceback.format_exc())
        return NullTelegramBot()


telegram_bot = get_telegram_bot()
