from pathlib import Path

from village.custom_classes.change_cycle_base import ChangeCycleBase
from village.scripts.log import log


class ChangeCycle(ChangeCycleBase):
    """Runs on every day/night change, when there is no animal in the box.

    It keeps the default behavior (super().run() deletes the videos older
    than DAYS_OF_VIDEO_STORAGE, only the ones already synced if SAFE_DELETE
    is ON) and then writes in the events how many videos are left and how
    much space they take, to keep an eye on the disk from day to day.
    """

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        super().run()  # remove this line if you don't want the default cleanup

        videos = list(Path(self.directory).rglob("*.mp4"))
        gb = sum(video.stat().st_size for video in videos) / 1024**3
        log.info(f"Videos stored after the cycle change: {len(videos)} ({gb:.1f} GB)")
