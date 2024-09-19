# from village.pybpodapi.protocol import Bpod, StateMachine

# bpod = Bpod()

# sma = StateMachine(bpod)

# sma.add_state(
#     state_name="State0",
#     state_timer=3,
#     state_change_conditions={Bpod.Events.Tup: "exit"},
#     output_actions=[],
# )


# bpod.send_state_machine(sma)
# bpod.run_state_machine(sma)

# # # sma.add_state(
# # #     state_name="State2",
# # #     state_timer=0,
# # #     state_change_conditions={"Port1Out": "State1"},
# # #     output_actions=[],
# # # )


# bpod.send_state_machine(sma)
# bpod.run_state_machine(sma)

# bpod.close()


# import importlib
# import inspect
# import os
# import sys

# from village.classes.task import Task
# from village.settings import settings

# directory = settings.get("CODE_DIRECTORY")
# sys.path.append(directory)


# import virtual_mouse

# print("OK")

# settings = Settings(
#     main_settings,
#     corridor_settings,
#     sound_settings,
#     alarm_settings,
#     directory_settings,
#     screen_settings,
#     touchscreen_settings,
#     telegram_settings,
#     bpod_settings,
#     camera_settings,
#     motor_settings,
#     extra_settings,
# )

# import trial_plotter

# print("OK")

# import follow_the_light

# print("OK")

# import task_runner

# print("OK")

# python_files = []
# tasks = []

# for root, dirs, files in os.walk(directory):
#     for file in files:
#         if file.endswith(".py"):
#             python_files.append(os.path.join(root, file))

# for python_file in python_files:
#     relative_path = os.path.relpath(python_file, directory)
#     module_name = os.path.splitext(relative_path.replace(os.path.sep, "."))[0]
#     print(f"Importing {module_name} from {python_file}")
#     try:
#         module = importlib.import_module(module_name)
#         print("done")
#         clsmembers = inspect.getmembers(module, inspect.isclass)
#         print("clsmembers: ", clsmembers)
#         for _, cls in clsmembers:
#             print("cls: ", cls)
#             if issubclass(cls, Task) and cls != Task:
#                 print("is subclass")
#                 name = cls.__name__
#                 print(name)
#                 new_task = cls()
#                 new_task.name = name
#                 tasks.append(new_task)
#     except Exception as e:
#         print("Error importing " + module_name)
#         continue

# import time

# from gpiozero import Servo


# servo = Servo(
#     18,
#     min_pulse_width=0.5 / 1000,
#     max_pulse_width=2.5 / 1000,
# )

# servo.max()
# time.sleep(2)
# servo.mid()
# time.sleep(2)
# servo.min()
# time.sleep(2)


import logging

from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from village.settings import settings

token = settings.get("TELEGRAM_TOKEN")


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("hola")
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token("7603292828:AAGLPgSyUUxMtwRj2cacXBMuYHTlni5IIb0")
        .build()
    )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()


# chat = settings.get("TELEGRAM_CHAT")
# users = settings.get("TELEGRAM_USERS")


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     print("hola")
#     await update.message.reply_text("Hi! Use /set <seconds> to set a timer")


# print(token)
# application = Application.builder().token(token).build()

# application.add_handler(CommandHandler("start", start))
# # application.add_handler(CommandHandler("help", self.help))

# application.run_polling(allowed_updates=Update.ALL_TYPES)


# # def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
# #     user = str(update.effective_user)
# #     print("User: ", user)
# #     print("context: ", context)
# #     update.message.reply_text("Hi! Use /status <hours> to see the status.")

# # def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
# #     update.message.reply_text("Help!")


# input("Press Enter to exit")
