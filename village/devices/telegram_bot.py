import asyncio
import os
import threading
import time
import traceback
from urllib import parse, request

import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from village.classes.abstract_classes import TelegramBotBase
from village.devices.camera import cam_box, cam_corridor
from village.log import log
from village.manager import manager
from village.plots.corridor_plot import corridor_plot
from village.scripts import time_utils
from village.settings import settings


class TelegramBot(TelegramBotBase):
    def __init__(self) -> None:
        self.token = settings.get("TELEGRAM_TOKEN")
        self.chat = settings.get("TELEGRAM_CHAT")
        self.message = ""
        self.connected = False
        self.error_running = False
        self.error = ""

        self.thread = threading.Thread(target=self.botloop, daemon=True)
        self.thread.start()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = "Hi! Use /report <hours> to get a report of the last hours."
        await update.message.reply_text(text)

    def alarm(self, message: str) -> None:
        try:
            url = "https://api.telegram.org/bot%s/sendMessage" % self.token
            data = parse.urlencode({"chat_id": self.chat, "text": message})
            request.urlopen(url, data.encode("utf-8"))
        except Exception:
            log.error("Telegram error sending alarm", exception=traceback.format_exc())

    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            hours = int(context.args[0])
            if hours < 1:
                hours = 24
            elif hours > 240:  # 10 days max
                hours = 240
        except (ValueError, IndexError, TypeError):
            hours = 24

        try:
            report, _, _, _ = manager.create_report(hours)
            await update.message.reply_text(report)
        except Exception:
            log.error(
                "Telegram error creating report", exception=traceback.format_exc()
            )

    async def cam(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        try:
            path = os.path.join(settings.get("VIDEOS_DIRECTORY"), "PLOT.jpg")
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
        self.application = ApplicationBuilder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.start))
        self.application.add_handler(CommandHandler("report", self.report))
        self.application.add_handler(CommandHandler("plot", self.plot))
        self.application.add_handler(CommandHandler("cam", self.cam))

        await self.application.initialize()
        await self.application.updater.start_polling()
        await self.application.start()
        self.connected = True
        while True:
            await asyncio.sleep(1)

    async def botloop_starttask(self) -> None:
        bot_routine = asyncio.create_task(self.main())
        await bot_routine

    def botloop(self) -> None:
        try:
            asyncio.run(self.botloop_starttask())
        except Exception:
            self.error_running = True
            log.error("Telegram error", exception=traceback.format_exc())


def get_telegram_bot() -> TelegramBotBase:
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
            return TelegramBotBase()
        else:
            log.error("Could not initialize telegram bot, time expired")
            return TelegramBotBase()
    except Exception:
        log.error("Could not initialize telegram bot", exception=traceback.format_exc())
        return TelegramBotBase()


telegram_bot = get_telegram_bot()
