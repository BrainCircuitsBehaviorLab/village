from typing import Any, get_args

from PyQt5.QtCore import QSettings

from village.classes.enums import (
    Actions,
    Active,
    AreaActive,
    Color,
    Cycle,
    Info,
    ScreenActive,
    SuperEnum,
)


class Setting:
    def __init__(
        self, key: str, factory_value: Any, value_type: type, description: str
    ) -> None:
        """A class containing the name of a particular setting,
        its factory (default) value, the type of the value and a description.
        The type can be: int, float, str, enum, list[int], list[str], list[enum].
        When the type is an enum or list[enum] the factory value contains the
        string representation of the enum."""
        self.key: str = key
        self.value: Any = factory_value
        self.value_type: type = value_type
        self.description: str = description

        self.type0: type = (
            value_type.__origin__ if hasattr(value_type, "__origin__") else value_type
        )
        try:
            self.type1: type | None = get_args(value_type)[0]
        except (IndexError, TypeError):
            self.type1 = None


class Settings:
    """The settings of the system. They are grouped in different categories."""

    def __init__(
        self,
        main_settings: list[Setting],
        corridor_settings: list[Setting],
        sound_settings: list[Setting],
        alarm_settings: list[Setting],
        directory_settings: list[Setting],
        screen_settings: list[Setting],
        touchscreen_settings: list[Setting],
        telegram_settings: list[Setting],
        bpod_settings: list[Setting],
        camera_settings: list[Setting],
        motor_settings: list[Setting],
        extra_settings: list[Setting],
    ) -> None:

        self.main_settings = main_settings
        self.corridor_settings = corridor_settings
        self.sound_settings = sound_settings
        self.alarm_settings = alarm_settings
        self.directory_settings = directory_settings
        self.screen_settings = screen_settings
        self.touchscreen_settings = touchscreen_settings
        self.telegram_settings = telegram_settings
        self.bpod_settings = bpod_settings
        self.camera_settings = camera_settings
        self.motor_settings = motor_settings
        self.extra_settings = extra_settings

        self.saved_settings = QSettings("village", "village")

        self.restorable_settings = (
            main_settings
            + corridor_settings
            + sound_settings
            + alarm_settings
            + directory_settings
            + screen_settings
            + touchscreen_settings
            + bpod_settings
        )

        self.all_settings = (
            self.restorable_settings
            + telegram_settings
            + camera_settings
            + motor_settings
            + extra_settings
        )

        self.create_factory_settings_if_first_launch()
        self.replace_extra_settings()

    def restore_factory_settings(self) -> None:
        for s in self.restorable_settings:
            self.saved_settings.setValue(s.key, s.value)

    def create_factory_settings(self) -> None:
        for s in self.all_settings:
            self.saved_settings.setValue(s.key, s.value)

    def replace_extra_settings(self) -> None:
        for s in self.extra_settings:
            self.saved_settings.setValue(s.key, s.value)

    def create_factory_settings_if_first_launch(self) -> None:
        if self.get("FIRST_LAUNCH") is None:
            self.create_factory_settings()

    def get(self, key: str) -> Any:
        """Get the value of a setting."""
        type = next((s.value_type for s in self.all_settings if s.key == key), None)
        try:
            if type == str:
                return self.saved_settings.value(key)
            elif type == int:
                return int(str(self.saved_settings.value(key)))
            elif type == float:
                return float(self.saved_settings.value(key))
            elif type == Active:
                return Active(self.saved_settings.value(key))
            elif type == Color:
                return Color(self.saved_settings.value(key))
            elif type == Actions:
                return Actions(self.saved_settings.value(key))
            elif type == Info:
                return Info(self.saved_settings.value(key))
            elif type == Cycle:
                return Cycle(self.saved_settings.value(key))
            elif type == ScreenActive:
                return ScreenActive(self.saved_settings.value(key))
            elif type == AreaActive:
                return AreaActive(self.saved_settings.value(key))
            elif type == list[str]:
                return self.saved_settings.value(key)
            elif type == list[int]:
                try:
                    return list(map(int, self.saved_settings.value(key)))
                except ValueError:
                    return [0] * len(self.saved_settings.value(key))
            elif type == list[Active]:
                return [Active(v) for v in self.saved_settings.value(key)]
            else:
                return self.saved_settings.value(key)
        except ValueError:
            return None

    def get_text(self, key: str) -> str:
        """Get the string representation of the value of a setting."""
        return str(self.saved_settings.value(key))

    def get_values(self, key: str) -> list:
        """Get the possible values of a setting when it is a enum or list of enums"""
        type0 = next((s.type0 for s in self.all_settings if s.key == key), None)
        type1 = next((s.type1 for s in self.all_settings if s.key == key), None)
        if type0 is None:
            return []
        elif issubclass(type0, SuperEnum):
            return type0.values()
        elif type1 is None:
            return []
        elif issubclass(type1, SuperEnum):
            return type1.values()
        else:
            return []

    def get_index(self, key: str) -> int:
        """Get the index of the value of a setting when it is a enum or list of enums"""
        type0 = next((s.type0 for s in self.all_settings if s.key == key), None)
        if type0 is None:
            return 0
        elif issubclass(type0, SuperEnum):
            return type0.keys().index(self.saved_settings.value(key))
        else:
            return 0

    def get_indices(self, key: str) -> list[int]:
        """Get the index of the value of a setting when it is a enum or list of enums"""
        type1 = next((s.type1 for s in self.all_settings if s.key == key), None)
        if type1 is None:
            return []
        elif issubclass(type1, SuperEnum):
            values = self.saved_settings.value(key)
            return [type1.keys().index(v) for v in values]
        else:
            return []

    def get_description(self, key: str) -> str:
        """Get the description of a setting."""
        return next((s.description for s in self.all_settings if s.key == key), "")

    def get_type(self, key: str) -> type | None:
        """Get the type of a setting."""
        return next((s.value_type for s in self.all_settings if s.key == key), None)

    def set(self, key: str, value: Any) -> None:
        self.saved_settings.setValue(key, value)

    def sync(self) -> None:
        # force to save the settings in disk,
        # only necessary when the application is not closed but reloaded
        self.saved_settings.sync()

    def print(self) -> None:
        for s in self.all_settings:
            print(s.key, self.get(s.key), s.value, s.value_type)
