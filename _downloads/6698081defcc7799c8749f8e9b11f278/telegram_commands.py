import shutil
import time
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from village.custom_classes.telegram_command_base import TelegramCommandBase
from village.settings import settings


class DiskCommand(TelegramCommandBase):
    """/disk: replies with the free space left on the Raspberry Pi disk."""

    command = "disk"
    description = "Free space left on the disk"

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        total, used, free = shutil.disk_usage("/")
        await update.message.reply_text(
            f"Free disk space: {free / 1024**3:.1f} GB "
            f"of {total / 1024**3:.1f} GB ({100 * free / total:.0f}%)"
        )


class VideosCommand(TelegramCommandBase):
    """/videos [days]: replies with how many videos are stored and how much
    space they take. With a number of days (/videos 2), only the videos
    recorded in the last days are counted.

    The words written after the command arrive in context.args, as strings.
    """

    command = "videos"
    description = "Videos stored, e.g. /videos or /videos 2 (last 2 days)"

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            days = float(context.args[0]) if context.args else None
        except ValueError:
            await update.message.reply_text("Usage: /videos or /videos <days>")
            return

        videos = list(Path(settings.get("VIDEOS_DIRECTORY")).rglob("*.mp4"))
        if days is not None:
            since = time.time() - days * 24 * 60 * 60
            videos = [video for video in videos if video.stat().st_mtime >= since]
        gb = sum(video.stat().st_size for video in videos) / 1024**3

        period = "" if days is None else f" in the last {context.args[0]} days"
        await update.message.reply_text(f"{len(videos)} videos{period}, {gb:.1f} GB")
