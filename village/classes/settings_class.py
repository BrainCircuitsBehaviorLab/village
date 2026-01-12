from typing import Any, get_args

from PyQt5.QtCore import QSettings

from village.classes.enums import (
    Actions,
    Active,
    AreaActive,
    Color,
    ControllerEnum,
    Cycle,
    Info,
    ScreenActive,
    SuperEnum,
    SyncType,
)


class Setting:
    """A class representing a single configuration setting.

    Attributes:
        key (str): The name/identifier of the setting.
        value (Any): The current value of the setting.
        value_type (type): The expected type of the value (e.g., int, float, str, enum).
        description (str): A description of what the setting controls.
        type0 (type): The base type (e.g., list if value_type is list[int]).
        type1 (type | None): The inner type for lists (e.g., int if value_type is list[int]).
    """

    def __init__(
        self, key: str, factory_value: Any, value_type: type, description: str
    ) -> None:
        """Initialize a new Setting.

        Args:
            key (str): The name of the setting.
            factory_value (Any): The default value. For enums, this is the string representation.
            value_type (type): The type of the value.
            description (str): A brief description of the setting.
        """
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
    """Manages system settings, including storage, retrieval, and grouping.

    Settings are grouped by category (main, sound, screen, etc.) and backed by
    QSettings for persistent storage.
    """

    def __init__(
        self,
        main_settings: list[Setting],
        sound_settings: list[Setting],
        screen_settings: list[Setting],
        touchscreen_settings: list[Setting],
        telegram_settings: list[Setting],
        directory_settings: list[Setting],
        sync_settings: list[Setting],
        server_settings: list[Setting],
        device_settings: list[Setting],
        hourly_alarm_settings: list[Setting],
        cycle_alarm_settings: list[Setting],
        session_alarm_settings: list[Setting],
        cam_framerate_settings: list[Setting],
        corridor_settings: list[Setting],
        extra_settings: list[Setting],
        controller_settings: list[Setting],
        bpod_settings: list[Setting],
        camera_settings: list[Setting],
        motor_settings: list[Setting],
        visual_settings: list[Setting],
        hidden_settings: list[Setting],
    ) -> None:

        self.main_settings = main_settings
        self.sound_settings = sound_settings
        self.screen_settings = screen_settings
        self.touchscreen_settings = touchscreen_settings
        self.telegram_settings = telegram_settings
        self.directory_settings = directory_settings
        self.sync_settings = sync_settings
        self.server_settings = server_settings
        self.device_settings = device_settings
        self.hourly_alarm_settings = hourly_alarm_settings
        self.cycle_alarm_settings = cycle_alarm_settings
        self.session_alarm_settings = session_alarm_settings
        self.cam_framerate_settings = cam_framerate_settings
        self.corridor_settings = corridor_settings
        self.extra_settings = extra_settings
        self.controller_settings = controller_settings
        self.bpod_settings = bpod_settings
        self.camera_settings = camera_settings
        self.motor_settings = motor_settings
        self.visual_settings = visual_settings
        self.hidden_settings = hidden_settings
        self.saved_settings = QSettings("village", "village")

        self.restorable_settings = (
            main_settings
            + sound_settings
            + screen_settings
            + touchscreen_settings
            + sync_settings
            + server_settings
            + device_settings
            + hourly_alarm_settings
            + cycle_alarm_settings
            + session_alarm_settings
            + cam_framerate_settings
            + corridor_settings
            + extra_settings
            + controller_settings
            + bpod_settings
            + visual_settings
        )

        self.all_settings = (
            self.restorable_settings
            + telegram_settings
            + directory_settings
            + camera_settings
            + motor_settings
            + hidden_settings
        )

        self.check_settings()

    def restore_factory_settings(self) -> None:
        """Reset all restorable settings to their factory default values."""
        for s in self.restorable_settings:
            self.saved_settings.setValue(s.key, s.value)

    def restore_visual_settings(self) -> None:
        """Reset visual settings to their factory default values."""
        for s in self.visual_settings:
            self.saved_settings.setValue(s.key, s.value)

    def restore_directory_settings(self) -> None:
        """Reset directory settings to their factory default values."""
        for s in self.directory_settings:
            self.saved_settings.setValue(s.key, s.value)

    def create_factory_settings(self) -> None:
        """Initialize all settings with their factory defaults in QSettings."""
        for s in self.all_settings:
            self.saved_settings.setValue(s.key, s.value)

    def add_new_settings(self) -> None:
        """Add any missing settings to QSettings with their default values."""
        for s in self.all_settings:
            if s.key not in self.saved_settings.allKeys():
                self.saved_settings.setValue(s.key, s.value)

    def check_settings(self) -> None:
        """Ensure all required settings exist in storage.

        If it's the first launch, creates all factory settings.
        Otherwise, adds any new settings that are missing.
        """
        if self.get("FIRST_LAUNCH") is None:
            self.create_factory_settings()
        else:
            self.add_new_settings()

    def get(self, key: str) -> Any:
        """Retrieve the value of a setting.

        Args:
            key (str): The identifier of the setting.

        Returns:
            Any: The value of the setting converted to its appropriate type,
            or None if the setting or value is invalid.
        """
        setting = next((s for s in self.all_settings if s.key == key), None)
        if setting is None:
            return None
        type = setting.value_type

        val = self.saved_settings.value(key)
        if val is None:
            return setting.value

        # If QSettings returns a QVariant/PyQt object/string that is not the value we expect
        # but contains "QSettings", it's likely a Sphinx build artifact or mock issue.
        val_str = str(val)
        if "QSettings" in val_str or "PyQt5" in val_str:
            return setting.value

        str_value = str(val)
        try:
            if type == str:
                return str_value
            elif type == int:
                return int(str_value)
            elif type == float:
                return float(str_value)
            elif type == Active:
                return Active(str_value)
            elif type == Color:
                return Color(str_value)
            elif type == ControllerEnum:
                return ControllerEnum(str_value)
            elif type == SyncType:
                return SyncType(str_value)
            elif type == Actions:
                return Actions(str_value)
            elif type == Info:
                return Info(str_value)
            elif type == Cycle:
                return Cycle(str_value)
            elif type == ScreenActive:
                return ScreenActive(str_value)
            elif type == AreaActive:
                return AreaActive(str_value)
            elif type == list[str]:
                return self.saved_settings.value(key)
            elif type == list[int]:
                try:
                    return list(map(int, self.saved_settings.value(key)))
                except ValueError:
                    return [0] * len(self.saved_settings.value(key))
            elif type == list[float]:
                try:
                    return list(map(float, self.saved_settings.value(key)))
                except ValueError:
                    return [0.0] * len(self.saved_settings.value(key))
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
            print(s.key)
            print("value:", self.get(s.key))
            print("value_type:", s.value_type)
            print("default_value:", s.value)
            print("")
