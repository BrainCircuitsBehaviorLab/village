import datetime

import sounddevice as sd
from PyQt5.QtWidgets import QLayout

from village.classes.protocols import LogProtocol


class Utils:
    def __init__(self) -> None:
        pass

    @staticmethod
    def now_string() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def now_string_for_filename() -> str:
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def log(
        self,
        description: str,
        type: str = "INFO",
        subject: str = "",
        exception: Exception | None = None,
        destinations: list[LogProtocol] = [],
    ) -> None:
        date = self.now_string()
        msg = date + "  " + type + "  " + subject + "  " + description
        if exception is None:
            print(msg)
        else:
            print(msg + str(exception))

        for d in destinations:
            d.log(date, type, subject, description)

    def delete_all_elements(self, layout: QLayout) -> None:
        for i in reversed(range(layout.count())):
            layoutItem = layout.itemAt(i)
            if layoutItem is not None:
                if layoutItem.widget() is not None:
                    widgetToRemove = layoutItem.widget()
                    widgetToRemove.deleteLater()
                else:
                    if layoutItem.layout() is not None:
                        self.delete_all_elements(layoutItem.layout())

    def get_sound_devices(self) -> list[str]:
        devices = sd.query_devices()
        devices_str = [d["name"] for d in devices]
        return devices_str


utils = Utils()
