import asyncio
import threading
import time
import traceback
from urllib import parse, request

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from village.devices.camera import cam_box, cam_corridor
from village.rt_plots import rt_plots
from village.settings import settings
from village.utils import utils


class TelegramBot:
    def __init__(self) -> None:
        self.token = settings.get("TELEGRAM_TOKEN")
        self.users = settings.get("TELEGRAM_USERS")
        self.chat = settings.get("TELEGRAM_CHAT")
        self.user = ""
        self.message = ""

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Hi! Use /status <hours> to see the status.")

    def alarm(self, subject: str, message: str) -> None:
        try:
            url = "https://api.telegram.org/bot%s/sendMessage" % self.token
            utils.log(message, subject=subject, type="ALARM")
            data = parse.urlencode({"chat_id": self.chat, "text": message})

            request.urlopen(url, data.encode("utf-8"))
        except Exception:
            utils.log("Telegram error", exception=traceback.format_exc())

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            hours = int(context.args[0])
            if hours < 1:
                hours = 24
            elif hours > 240:  # 10 days max
                hours = 240
        except (ValueError, IndexError, TypeError):
            hours = 24

        try:
            user_id = str(update.effective_user.id)
            if user_id not in self.users:
                utils.log("WARNING: New Telegram User ID: " + user_id)
            else:
                status = rt_plots.telegram_data(hours=hours)
                await update.message.reply_text(status)
        except Exception:
            utils.log("Telegram error", exception=traceback.format_exc())

    async def cam(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            user_id = str(update.effective_user.id)
            if user_id not in self.users:
                utils.log("WARNING: New Telegram User ID: " + user_id)
            else:
                cam_corridor.take_picture()
                cam_box.take_picture()
                time.sleep(1)
                with open(cam_corridor.path_picture, "rb") as picture_corridor:
                    await update.message.reply_photo(photo=picture_corridor)
                with open(cam_box.path_picture, "rb") as picture_box:
                    await update.message.reply_photo(photo=picture_box)
        except Exception:
            utils.log("Telegram error", exception=traceback.format_exc())

    async def plot(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            days = int(context.args[0])
            if days < 1:
                days = 3
            elif days > 10:
                days = 10
        except (ValueError, IndexError, TypeError):
            days = 3
        try:
            user_id = str(update.effective_user.id)
            if user_id not in self.users:
                utils.log("WARNING: New Telegram User ID: " + user_id)
            else:
                rt_plots.plot(days)
                chrono = utils.Chrono()
                while rt_plots.running:
                    time.sleep(1)
                    if chrono.get_seconds() > 120:
                        utils.log("Plotting time out", type="ERROR")
                        break
                with open(rt_plots.plot_path, "rb") as picture:
                    await update.message.reply_photo(photo=picture)
        except Exception:
            utils.log("Telegram error", exception=traceback.format_exc())

    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            user_id = str(update.effective_user.id)
            if user_id not in self.users:
                utils.log("WARNING: New Telegram User ID: " + user_id)
            else:
                await self.status(update, context)
                await self.cam(update, context)
                await self.plot(update, context)
        except Exception:
            utils.log("Telegram error", exception=traceback.format_exc())

    async def main(self) -> None:
        self.application = ApplicationBuilder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.start))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("plot", self.plot))
        self.application.add_handler(CommandHandler("cam", self.cam))
        self.application.add_handler(CommandHandler("report", self.report))

        await self.application.initialize()
        await self.application.updater.start_polling()
        await self.application.start()
        while True:
            await asyncio.sleep(1)

    async def botloop_starttask(self) -> None:
        bot_routine = asyncio.create_task(self.main())
        await bot_routine

    def botloop(self) -> None:
        asyncio.run(self.botloop_starttask())


telegram_bot = TelegramBot()

thread = threading.Thread(target=telegram_bot.botloop, daemon=True)
thread.start()
