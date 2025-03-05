import os
import threading

from village.settings import settings


class RTPlots:
    def __init__(self) -> None:
        self.hours = 24
        self.days = 3
        self.plot_path = os.path.join(settings.get("DATA_DIRECTORY"), "plot.png")

    def telegram_data(self, hours) -> str:
        self.hours = hours
        return "TODO: Implement me!"

    def plot(self, days) -> None:
        self.days = days
        plotting = threading.Thread(target=self.plot_thread, daemon=True)
        self.running = True
        plotting.start()

    def plot_thread(self) -> None:
        self.running = False


rt_plots = RTPlots()
