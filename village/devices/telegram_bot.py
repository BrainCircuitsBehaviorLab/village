# import os
# import threading
# import time
# from io import BytesIO
# from urllib import parse, request

# from PIL import Image

# # from telegram.ext import CommandHandler, Updater
# from telegram import Update
# from telegram.ext import (
#     Application,
#     CommandHandler,
#     ContextTypes,
#     MessageHandler,
#     filters,
# )

# from village import queues
# from village.devices.camera import cam_box, cam_corridor

# # from village.plots import plots
# from village.settings import settings
# from village.utils import utils

# # try:
# #     from user.rt_plots import fig
# # except:
# #     fig = None


# class TelegramBot:
#     def __init__(self) -> None:
#         self.token = settings.get("TELEGRAM_TOKEN")
#         self.chat = settings.get("TELEGRAM_CHAT")
#         self.users = settings.get("TELEGRAM_USERS")
#         self.thread = threading.Thread(target=self.run, daemon=True)
#         self.thread.start()

#     def run(self) -> None:
#         application = Application.builder().token(self.token).build()

#         application.add_handler(CommandHandler("start", self.start))
#         application.add_handler(CommandHandler("help", self.help))

#         application.add_handler(
#             MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo)
#         )

#         application.run_polling(allowed_updates=Update.ALL_TYPES)

#         # dp.add_handler(CommandHandler("start", self.start))
#         # dp.add_handler(CommandHandler("help", self.start))
#         # dp.add_handler(CommandHandler("status", self.status, pass_args=True))
#         # dp.add_handler(CommandHandler("plot", self.plot, pass_args=True))
#         # dp.add_handler(CommandHandler("cam", self.cam, pass_args=True))
#         # dp.add_handler(CommandHandler("report", self.report, pass_args=True))
#         # updater.start_polling()

#     async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#         # user = update.effective_user
#         await update.message.reply_text("Hi! Use /status <hours> to see the status.")

#     async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#         """Send a message when the command /help is issued."""
#         await update.message.reply_text("Help!")

#     def alarm(self, subject: str, message: str) -> None:
#         try:
#             url = "https://api.telegram.org/bot%s/sendMessage" % self.token
#             utils.log(message, subject=subject, type="ALARM")
#             data = parse.urlencode({"chat_id": self.chat, "text": message})

#             request.urlopen(url, data.encode("utf-8"))
#         except Exception as e:
#             utils.log("Telegram error", exception=e)

#     def status(self, update, context) -> None:
#         try:
#             hours = int(context.args[0])
#             if hours < 1:
#                 hours = 24
#             elif hours > 240:  # 10 days max
#                 hours = 240
#         except (ValueError, IndexError, TypeError):
#             hours = 24

#         try:
#             user_id = str(update.effective_user.id)

#             if user_id not in self.users():
#                 utils.log("WARNING: New Telegram User ID: " + user_id)

#             else:
#                 # data, error_mice_list = rt_plots.telegram_data(hours=hours)
#                 update.message.reply_text("probando")
#         except Exception as e:
#             utils.log("Telegram error", exception=e)

#     def cam(self, update, context) -> None:

#         try:
#             user_id = str(update.effective_user.id)

#             if user_id not in self.users():
#                 utils.log("WARNING: New Telegram User ID: " + user_id)

#             else:

#                 try:
#                     frame1 = cam_corridor.image_queue.get(timeout=1)
#                     img1 = Image.fromarray(frame1)
#                     stream1 = BytesIO()
#                     img1.save(stream1, format="JPEG")
#                     stream1.seek(0)
#                     update.message.reply_photo(photo=stream1)
#                 except Exception:
#                     pass

#                 try:
#                     frame2 = cam_box.image_queue.get(timeout=1)
#                     img2 = Image.fromarray(frame2)
#                     stream2 = BytesIO()
#                     img2.save(stream2, format="JPEG")
#                     stream2.seek(0)
#                     update.message.reply_photo(photo=stream2)
#                 except Exception:
#                     pass

#         except Exception as e:
#             utils.log("Telegram error", exception=e)

#     def plot(self, update, context) -> None:

#         try:
#             user_id = str(update.effective_user.id)

#             if user_id not in self.users():
#                 utils.log("WARNING: New Telegram User ID: " + user_id)

#             else:

#                 try:
#                     days = int(context.args[0])
#                     if days < 1:
#                         days = 3
#                     elif days > 10:
#                         days = 10
#                 except (ValueError, IndexError, TypeError):
#                     days = 3

#                 try:
#                     photo = os.path.join(settings.DATA_DIRECTORY, "plots.jpg")
#                     utils.x_max = days
#                     time.sleep(1)
#                     queues.update_plots.put(True)
#                     time.sleep(20)
#                     update.message.reply_photo(photo=open(photo, "rb"))
#                 except Exception:
#                     pass
#         except Exception as e:
#             utils.log("Telegram error", exception=e)

#     def report(self, update, context) -> None:
#         try:
#             user_id = str(update.effective_user.id)

#             if user_id not in self.users():
#                 utils.log("WARNING: New Telegram User ID: " + user_id)

#             else:
#                 self.status(update, context)
#                 self.cam(update, context)
#                 self.plot(update, context)
#         except Exception as e:
#             utils.log("Telegram error", exception=e)


# telegram_bot = TelegramBot()
