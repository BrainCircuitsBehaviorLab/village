import json
from typing import Any

import pandas as pd


class TrainingError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class Settings:
    def __init__(self) -> None:
        self.next_task = "-1"
        self.refractary_period = -1
        self.minimum_duration: float = -1
        self.maximum_duration: float = -1


class Training:
    def __init__(self) -> None:
        self.default_settings = Settings()
        self.settings = Settings()
        self.subject = "None"
        self.df: pd.DataFrame = pd.DataFrame()

    def check_variables(self) -> None:
        self.settings.refractary_period = int(self.settings.refractary_period)
        self.settings.minimum_duration = float(self.settings.minimum_duration)
        self.settings.maximum_duration = float(self.settings.maximum_duration)
        if self.settings.next_task == "-1":
            raise TrainingError("The variable next_task is required (must be a string)")
        if self.settings.refractary_period < 0:
            raise TrainingError(
                """
                The variable refractary_period is required (must be a positive integer)
                """
            )
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
        raise TrainingError("The method default_training_settings(self) is required")

    def update_training_settings(self) -> None:
        raise TrainingError("The method update_training_settings(self) is required")

    # DO NOT OVERWRITE THESE METHODS
    def copy_settings(self) -> None:
        self.default_training_settings()
        for attr in vars(self.settings):
            setattr(self.default_settings, attr, getattr(self.settings, attr))
        self.check_variables()

    def get_settings_names(self) -> list[str]:
        default_properties = [
            "next_task",
            "minimum_duration",
            "maximum_duration",
            "refractary_period",
        ]
        extra_properties = [
            prop
            for prop in vars(self.default_settings)
            if prop not in default_properties
        ]
        properties = default_properties + extra_properties
        return properties

    # def get_types(self) -> dict[str, Any]:
    #     types = {}
    #     for name in self.get_settings_names():
    #         if hasattr(self.settings, name):
    #             value = getattr(self.settings, name)
    #             types[name] = type(value)
    #     return types

    def get_dict(self) -> dict[str, Any]:
        properties = {}
        for name in self.get_settings_names():
            if hasattr(self.settings, name):
                value = getattr(self.settings, name)
                properties[name] = value
        return properties

    def get_default_dict(self) -> dict[str, Any]:
        properties = {}
        for name in self.get_settings_names():
            if hasattr(self.default_settings, name):
                value = getattr(self.default_settings, name)
                properties[name] = value
        return properties

    def get_jsonstring(self) -> str:
        return json.dumps(self.get_dict())

    def load_settings_from_dict(self, current_dict: dict[str, Any]) -> None:
        current_dict = self.correct_types_in_dict(current_dict)
        for key, value in self.get_default_dict().items():
            if key in current_dict:
                setattr(self.settings, key, current_dict[key])
            else:
                setattr(self.settings, key, value)

    def load_settings_from_jsonstring(self, current_value: str) -> None:
        try:
            current_dict = json.loads(current_value)
        except Exception:
            current_dict = {}
        if not isinstance(current_dict, dict):
            current_dict = {}
        self.load_settings_from_dict(current_dict)

    def restore(self) -> None:
        for key, value in self.get_default_dict().items():
            setattr(self.settings, key, value)

    def get_jsonstring_from_jsonstring(self, current_value: str) -> str:
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

    def correct_types_in_dict(self, current_dict: dict[str, Any]) -> dict[str, Any]:
        default_dict: dict[str, Any] = self.get_default_dict()
        for key, value in current_dict.items():
            if key in default_dict:
                try:
                    if isinstance(default_dict[key], int):
                        value = int(value)
                    elif isinstance(default_dict[key], float):
                        value = float(value)
                    elif isinstance(default_dict[key], bool):
                        value = value.lower() in ["true", "1", "yes"]
                    elif isinstance(default_dict[key], list):
                        value = eval(value) if value.startswith("[") else str(value)
                    elif isinstance(default_dict[key], dict):
                        value = eval(value) if value.startswith("{") else str(value)
                except Exception:
                    pass
                current_dict[key] = value
        return current_dict

    def get_string(self) -> str:
        dict = self.get_dict()
        new_dict = self.correct_types_in_dict(dict)
        return json.dumps(new_dict)
