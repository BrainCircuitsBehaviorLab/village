import json
from typing import Any


class TrainingProtocolError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)


class Training:
    def __init__(self) -> None:
        self.next_task = "-1"
        self.refractary_period = -1
        self.maximum_number_of_trials: int = -1
        self.minimum_duration: float = -1
        self.maximum_duration: float = -1

    def check_variables(self) -> None:
        self.refractary_period = int(self.refractary_period)
        self.maximum_number_of_trials = int(self.maximum_number_of_trials)
        if self.maximum_number_of_trials == 0:
            self.maximum_number_of_trials = 1000000
        self.minimum_duration = float(self.minimum_duration)
        self.maximum_duration = float(self.maximum_duration)
        if self.next_task == "-1":
            raise TrainingProtocolError(
                "The variable next_task is required (must be a string)"
            )
        if self.refractary_period < 0:
            raise TrainingProtocolError(
                """
                The variable refractary_period is required (must be a positive integer)
                """
            )
        if self.maximum_number_of_trials < 0:
            raise TrainingProtocolError(
                """The variable maximum_number_of_trials is required
                (must be a positive integer or zero for infinite trials)"""
            )
        if self.minimum_duration < 0:
            raise TrainingProtocolError(
                "The variable minimum_duration is required (must be a positive float)"
            )
        if self.maximum_duration < 0:
            raise TrainingProtocolError(
                "The variable maximum_duration is required (must be a positive float)"
            )

    # OVERWRITE THIS METHOD IN YOUR TRAINING PROTOCOL
    def update_training_settings(self) -> None:
        raise TrainingProtocolError(
            "The method update_training_settings(self) is required"
        )

    # DO NOT OVERWRITE THESE METHODS
    def get_settings_names(self) -> list[str]:
        default_properties = [
            "next_task",
            "minimum_duration",
            "maximum_duration",
            "maximum_number_of_trials",
            "refractary_period",
        ]
        extra_properties = [
            prop
            for prop in dir(self)
            if not callable(getattr(self, prop))
            and not prop.startswith("_")
            and prop not in default_properties
        ]
        properties = default_properties + extra_properties
        return properties

    def get_dictionary(self) -> dict[str, Any]:
        properties = {}
        for name in self.get_settings_names():
            if hasattr(self, name):
                value = getattr(self, name)
                properties[name] = value
        return properties

    def get_json(self) -> str:
        return json.dumps(self.get_dictionary())

    def get_dict_from_dict(self, current_dict: dict[str, Any]) -> dict[str, Any]:
        new_dict: dict[str, Any] = self.get_dictionary()
        for key in new_dict.keys():
            try:
                new_dict[key] = current_dict[key]
            except KeyError:
                pass
        return new_dict

    def get_dict_from_jsonstring(self, current_value: str) -> dict[str, Any]:
        try:
            current_dict: dict[str, Any] = json.loads(current_value)
        except Exception:
            current_dict = {}

        return self.get_dict_from_dict(current_dict)

    def get_jsonstring_from_dict(self, current_dict: dict[str, Any]) -> str:
        new_dict: dict[str, Any] = self.get_dict_from_dict(current_dict)
        return json.dumps(new_dict)

    def get_jsonstring_from_jsonstring(self, current_value: str) -> str:
        new_dict: dict[str, Any] = self.get_dict_from_jsonstring(current_value)
        return self.get_jsonstring_from_dict(new_dict)
