import asyncio
import datetime
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

# increase alarm message salience!
ALARM_EMOJI = "⚠️⚠️⚠️"  # ⚠️💀


class Alarm:
    """An alarm waiting to be acknowledged.

    Attributes:
        message (str): The text of the alarm.
        start (datetime): When the alarm was triggered the first time.
        repeats (int): How many times it has been resent.
        next_due (datetime): When it has to be resent again.
        message_id (int): The message showing the alarm in the chat, 0 if none.
    """

    def __init__(self, message: str, minutes: int) -> None:
        """Initializes an Alarm due in minutes.

        Args:
            message (str): The text of the alarm.
            minutes (int): Minutes until the first reminder.
        """
        self.message = message
        self.start = time_utils.now()
        self.repeats = 0
        self.next_due = self.start + datetime.timedelta(minutes=minutes)
        self.message_id = 0

    def text(self) -> str:
        """Builds the message shown in the chat.

        Returns:
            str: The alarm, with the time it started and the number of repeats.
        """
        text = ALARM_EMOJI + self.message
        text += "\n\nalarm at " + self.start.strftime("%H:%M")
        if self.repeats > 0:
            text += ", repeated " + str(self.repeats) + " times"
            text += " (last " + time_utils.now().strftime("%H:%M") + ")"
        return text


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
        self.pending: dict[int, Alarm] = {}
        self.alarm_id = 0

        self.thread = threading.Thread(target=self.botloop, daemon=True)
        self.thread.start()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Responds to the /start command.

        Args:
            update (Update): The update object.
            context (ContextTypes.DEFAULT_TYPE): The context object.
        """
        text = "Hi! Use /report <hours> to get a report of the last hours.\n"
        text += "Use /mice_checked to confirm that you checked the mice today."
        await update.message.reply_text(text)

    def alarm(self, message: str, repeat: bool = False, report: bool = False) -> None:
        """Sends an alarm message to the configured chat.

        Repeatable alarms are kept in self.pending and resent every
        TELEGRAM_REPEAT_MINUTES until acknowledged, either with the button in
        telegram or with the ALARM button in the GUI.

        Args:
            message (str): The message content.
            repeat (bool): True to resend the alarm until it is acknowledged.
            report (bool): True for the daily report, sent without the emoji
            so that it only marks the messages that need attention.
        """
        if not repeat:
            self.send(("" if report else ALARM_EMOJI) + message, None)
            return

        # keep only one pending with same first line (because is same alarm).
        first_line = message.split("\n")[0]
        self.pending = {
            k: v
            for k, v in self.pending.items()
            if v.message.split("\n")[0] != first_line
        }
        self.alarm_id += 1
        alarm = Alarm(message, self.repeat_minutes())
        self.pending[self.alarm_id] = alarm
        alarm.message_id = self.send(alarm.text(), self.alarm_id)

    def repeat_minutes(self) -> int:
        """Minutes between reminders"""
        return settings.get("TELEGRAM_REPEAT_MINUTES") or 30

    def send(self, text: str, ack_id: int | None) -> int:
        """Sends a message, optionally with an acknowledge button.

        Uses plain http because it is called from threads outside the bot
        asyncio loop.

        Args:
            text (str): The message content.
            ack_id (int | None): Id of the alarm to acknowledge, if any.

        Returns:
            int: The id of the message sent, 0 if it could not be sent.
        """
        try:
            url = "https://api.telegram.org/bot%s/sendMessage" % self.token
            values = {"chat_id": self.chat, "text": text}
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
            with request.urlopen(url, data.encode("utf-8"), timeout=10) as answer:
                return json.load(answer)["result"]["message_id"]
        except Exception:
            log.error("Telegram error sending alarm", exception=traceback.format_exc())
            return 0

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
                query.message.text + "\n\n✅ acknowledged by " + query.from_user.name
            )
        except Exception:
            log.error("Telegram error acknowledging", exception=traceback.format_exc())

    async def repeat_alarms(self) -> None:
        """Resends unacknowledged alarms, each one on its own schedule."""
        while True:
            await asyncio.sleep(30)
            for ack_id, alarm in list(self.pending.items()):
                if time_utils.now() < alarm.next_due:
                    continue
                alarm.repeats += 1
                minutes = self.repeat_minutes()
                alarm.next_due = time_utils.now() + datetime.timedelta(minutes=minutes)
                self.update(alarm, ack_id)

    def update(self, alarm: Alarm, ack_id: int) -> None:
        """Updates the alarm in the telegram chat, with number of repeats.
        Need to delete/send again otherwise no notification!

        Args:
            alarm (Alarm): The alarm to update.
            ack_id (int): Id used by its acknowledge button.
        """
        if alarm.message_id != 0:
            try:  # delete old message
                t = self.token
                url = "https://api.telegram.org/bot%s/deleteMessage" % t
                values = {"chat_id": self.chat, "message_id": alarm.message_id}
                data = parse.urlencode(values)
                request.urlopen(url, data.encode("utf-8"), timeout=10)
            except Exception:
                pass  # already gone or too old
        alarm.message_id = self.send(alarm.text(), ack_id)  # send update

    async def mice_checked(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Confirms with /mice_checked that the mice have been checked.

        Args:
            update (Update): The update object.
            context (ContextTypes.DEFAULT_TYPE): The context object.
        """
        try:
            manager.mice_checked(update.effective_user.name)
            await update.message.reply_text("Mice checked! 🐭")
        except Exception:
            log.error("Telegram error checking mice", exception=traceback.format_exc())

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

    def register_custom(self, commands: list) -> None:
        """Registers custom commands collected from the project code directory.

        Called from main after import_all has populated the list. add_handler
        works on the already-running application.

        Args:
            commands (list): TelegramCommandBase instances.
        """
        for c in commands:
            if c.command:
                self.application.add_handler(CommandHandler(c.command, c.handler))

    async def main(self) -> None:
        """Main asyncio loop for the bot application."""
        self.application = ApplicationBuilder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.start))
        self.application.add_handler(CommandHandler("report", self.report))
        self.application.add_handler(CommandHandler("plot", self.plot))
        self.application.add_handler(CommandHandler("cam", self.cam))
        self.application.add_handler(CommandHandler("mice_checked", self.mice_checked))
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
