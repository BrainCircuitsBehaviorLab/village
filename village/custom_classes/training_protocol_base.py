import json
from typing import Any, Tuple

import pandas as pd


class TrainingError(Exception):
    """Exception raised for errors in the TrainingProtocol class."""

    def __init__(self, message) -> None:
        super().__init__(message)


class Settings:
    """Class to hold training settings values."""

    def __init__(self) -> None:
        """Initializes default training settings."""
        self.next_task = "-1"
        self.refractory_period = -1
        self.minimum_duration: float = -1
        self.maximum_duration: float = -1
        self.observations: str = ""


class TrainingProtocolBase:
    """Base class for defining training protocols and managing settings.

    Training protocols dictate how settings change over sessions based on subject performance.
    """

    def __init__(self) -> None:
        """Initializes the TrainingProtocolBase instance."""
        self.default_settings = Settings()
        self.settings = Settings()
        self.subject = "None"
        self.last_task = "None"
        self.df: pd.DataFrame = pd.DataFrame()
        self.gui_tabs: dict[str, list[str]] = {}
        self.gui_tabs_restricted: dict[str, list[Any]] = {}
        self.define_gui_tabs()

    def check_variables(self) -> None:
        """Validates that all required settings are present and of the correct type.

        Raises:
            TrainingError: If a required variable is invalid or missing.
        """
        self.settings.refractory_period = int(self.settings.refractory_period)
        self.settings.minimum_duration = float(self.settings.minimum_duration)
        self.settings.maximum_duration = float(self.settings.maximum_duration)
        if self.settings.next_task == "-1":
            raise TrainingError("The variable next_task is required (must be a string)")
        if self.settings.refractory_period < 0:
            raise TrainingError("""
                The variable refractory_period is required (must be a positive integer)
                """)
        if self.settings.minimum_duration < 0:
            raise TrainingError(
                "The variable minimum_duration is required (must be a positive float)"
            )
        if self.settings.maximum_duration < 0:
            raise TrainingError(
                "The variable maximum_duration is required (must be a positive float)"
            )

    # OVERWRITE THESE METHOD IN YOUR TRAINING PROTOCOL
    def default_training_settings(self) -> None:
        """Sets the default values for the training settings. Must be overridden."""
        raise TrainingError("The method default_training_settings(self) is required")

    def update_training_settings(self) -> None:
        """Updates the settings based on performance. Must be overridden."""
        raise TrainingError("The method update_training_settings(self) is required")

    def define_gui_tabs(self) -> None:
        """Defines the tabs and organization for the GUI settings editor."""
        self.gui_tabs = {}
        self.gui_tabs_restricted = {}

    # DO NOT OVERWRITE THESE METHODS
    def copy_settings(self) -> None:
        """Copies current settings to default settings and validates them."""
        self.default_training_settings()
        for attr in vars(self.settings):
            setattr(self.default_settings, attr, getattr(self.settings, attr))
        self.check_variables()

    def get_settings_names(self) -> list[str]:
        """Returns a list of all setting names, including defaults and extras.

        Returns:
            list[str]: list of setting names.
        """
        default_properties = [
            "next_task",
            "minimum_duration",
            "maximum_duration",
            "refractory_period",
        ]
        observations = ["observations"]
        extra_properties = [
            prop
            for prop in vars(self.default_settings)
            if prop not in default_properties + observations
        ]
        properties = default_properties + extra_properties + observations

        return properties

    def get_dict(self, exclude: list[str] = []) -> dict[str, Any]:
        """Returns the current settings as a dictionary.

        Args:
            exclude (list[str], optional): List of keys to exclude. Defaults to [].

        Returns:
            dict[str, Any]: Dictionary of settings.
        """
        properties = {}
        for name in self.get_settings_names():
            if hasattr(self.settings, name) and name not in exclude:
                value = getattr(self.settings, name)
                properties[name] = value
        return properties

    def get_default_dict(self) -> dict[str, Any]:
        """Returns the default settings as a dictionary.

        Returns:
            dict[str, Any]: Dictionary of default settings.
        """
        properties = {}
        for name in self.get_settings_names():
            if hasattr(self.default_settings, name):
                value = getattr(self.default_settings, name)
                properties[name] = value
        return properties

    def get_jsonstring(self, exclude: list[str] = []) -> str:
        """Returns the current settings as a JSON string.

        Args:
            exclude (list[str], optional): List of keys to exclude. Defaults to [].

        Returns:
            str: JSON representation of settings.
        """
        return json.dumps(self.get_dict(exclude=exclude))

    def load_settings_from_dict(self, current_dict: dict[str, Any]) -> list[str]:
        """Loads settings from a dictionary, correcting types where necessary.

        Args:
            current_dict (dict[str, Any]): Dictionary containing new setting values.

        Returns:
            list[str]: List of keys that failed type correction.
        """
        wrong_keys, current_dict = self.correct_types_in_dict(current_dict)
        for key, value in self.get_default_dict().items():
            if key in current_dict:
                setattr(self.settings, key, current_dict[key])
            else:
                setattr(self.settings, key, value)
        return wrong_keys

    def load_settings_from_jsonstring(self, current_value: str) -> None:
        """Loads settings from a JSON string.

        Args:
            current_value (str): JSON string of settings.
        """
        try:
            current_dict = json.loads(current_value)
        except Exception:
            current_dict = {}
        if not isinstance(current_dict, dict):
            current_dict = {}
        self.load_settings_from_dict(current_dict)

    def restore(self) -> None:
        """Restores all settings to their default values."""
        for key, value in self.get_default_dict().items():
            setattr(self.settings, key, value)

    def get_jsonstring_from_jsonstring(self, current_value: str) -> str:
        """Merges a JSON string with defaults and returns a valid JSON string.

        Args:
            current_value (str): Input JSON string.

        Returns:
            str: Merged JSON string.
        """
        try:
            current_dict = json.loads(current_value)
        except Exception:
            current_dict = {}
        if not isinstance(current_dict, dict):
            current_dict = {}
        new_dict: dict[str, Any] = self.get_default_dict()
        for key in new_dict.keys():
            if key in current_dict:
                new_dict[key] = current_dict[key]
        return json.dumps(new_dict)

    def correct_types_in_dict(
        self, current_dict: dict[str, Any]
    ) -> Tuple[list[str], dict[str, Any]]:
        """Ensures that dictionary values match the types of default settings.

        Args:
            current_dict (dict[str, Any]): Input dictionary.

        Returns:
            Tuple[list[str], dict[str, Any]]: A tuple containing a list of keys with
            type errors and the corrected dictionary.
        """
        wrong_keys: list[str] = []
        default_dict: dict[str, Any] = self.get_default_dict()
        for key, value in current_dict.items():
            if key in default_dict:
                try:
                    if isinstance(default_dict[key], bool):
                        value = value.lower() in ["true", "1", "yes"]
                    elif isinstance(default_dict[key], int):
                        value = float(value)
                    elif isinstance(default_dict[key], float):
                        value = float(value)
                    elif isinstance(default_dict[key], list):
                        value = eval(value)
                    elif isinstance(default_dict[key], dict):
                        value = eval(value)
                except Exception:
                    wrong_keys.append(key)
                current_dict[key] = value
        return wrong_keys, current_dict

    def get_string(self) -> str:
        """Returns the settings as a JSON string with corrected types.

        Returns:
            str: JSON string of settings.
        """
        dict = self.get_dict()
        _, new_dict = self.correct_types_in_dict(dict)
        return json.dumps(new_dict)
