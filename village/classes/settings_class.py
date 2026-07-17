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
    OldVersion,
    PixelType,
    Samplerate,
    ScreenActive,
    SuperEnum,
    SyncType,
)


class Setting:
    """A class representing a single configuration setting.

    Attributes:
        key (str): The name/identifier of the setting.
        value (Any): The current default value of the setting.
        value_type (type): The full declared type of the value. Can be a
            simple type (``int``, ``float``, ``str``, an enum subclass) or a
            generic list type (``list[int]``, ``list[str]``, ``list[Active]``).
        description (str): A description of what the setting controls.
        base_type (type): The outer/container type extracted from
            ``value_type``. For simple types this equals ``value_type``
            itself; for generic lists it is ``list``.
        element_type (type | None): For list settings, the type of each
            element (e.g. ``int`` for ``list[int]``, ``Active`` for
            ``list[Active]``). ``None`` for non-list settings.
    """

    def __init__(
        self, key: str, factory_value: Any, value_type: type, description: str
    ) -> None:
        """Initialize a new Setting.

        Args:
            key (str): The name of the setting.
            factory_value (Any): The default value. For enums, this is the
                string representation.
            value_type (type): The full declared type. Can be a simple type
                (``int``, ``float``, ``str``, an enum subclass) or a generic
                list type (``list[int]``, ``list[Active]``, etc.).
            description (str): A brief description of the setting.
        """
        self.key: str = key
        self.value: Any = factory_value
        self.value_type: type = value_type
        self.description: str = description

        self.base_type: type = (
            value_type.__origin__ if hasattr(value_type, "__origin__") else value_type
        )
        try:
            self.element_type: type | None = get_args(value_type)[0]
        except (IndexError, TypeError):
            self.element_type = None


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
        led_strip_settings: list[Setting],
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
        self.led_strip_settings = led_strip_settings
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

        # main_settings is excluded on purpose: SYSTEM_NAME, USE_CORRIDOR and
        # USE_BOX_BOARD describe this specific machine's identity and physical
        # hardware, not trainable defaults, so a factory reset must not touch
        # them (same reasoning as directory_settings below).
        self.restorable_settings = (
            sound_settings
            + screen_settings
            + touchscreen_settings
            + sync_settings
            + server_settings
            + device_settings
            + led_strip_settings
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
            main_settings
            + self.restorable_settings
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
        for s in self.all_settings:
            old_value = self.get(s.key)
            if old_value is None:
                self.saved_settings.setValue(s.key, s.value)

    def restore_visual_settings(self) -> None:
        """Reset visual settings to their factory default values."""
        for s in self.visual_settings:
            self.saved_settings.setValue(s.key, s.value)

    def restore_directory_settings(self) -> None:
        """Reset directory settings to their factory default values."""
        for s in self.directory_settings:
            self.saved_settings.setValue(s.key, s.value)

    def restore_all_settings(self) -> None:
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
            self.restore_all_settings()
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

        # If QSettings returns a QVariant/PyQt object/string that is not the value
        # we expect but contains "QSettings", it's likely a Sphinx build
        # artifact or mock issue.
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
            elif type == OldVersion:
                return OldVersion(str_value)
            elif type == PixelType:
                return PixelType(str_value)
            elif type == Samplerate:
                return int(str_value)
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
        base_type = next((s.base_type for s in self.all_settings if s.key == key), None)
        element_type = next(
            (s.element_type for s in self.all_settings if s.key == key), None
        )
        if base_type is None:
            return []
        elif issubclass(base_type, SuperEnum):
            return base_type.values()
        elif element_type is None:
            return []
        elif issubclass(element_type, SuperEnum):
            return element_type.values()
        else:
            return []

    def get_index(self, key: str) -> int:
        """Get the index of the value of a setting when it is a enum or list of enums"""
        base_type = next((s.base_type for s in self.all_settings if s.key == key), None)
        if base_type is None:
            return 0
        elif issubclass(base_type, SuperEnum):
            return base_type.values().index(self.saved_settings.value(key))
        else:
            return 0

    def get_indices(self, key: str) -> list[int]:
        """Get the index of the value of a setting when it is a enum or list of enums"""
        element_type = next(
            (s.element_type for s in self.all_settings if s.key == key), None
        )
        if element_type is None:
            return []
        elif issubclass(element_type, SuperEnum):
            values = self.saved_settings.value(key)
            return [element_type.keys().index(v) for v in values]
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
