import json
from typing import Any

from village.custom_classes.training_protocol_base import TrainingProtocolBase


class Protocol(TrainingProtocolBase):
    def default_training_settings(self) -> None:
        settings: Any = self.settings  # the protocol adds its own settings
        settings.next_task = "Task"
        settings.refractory_period = 3600
        settings.minimum_duration = 600
        settings.maximum_duration = 900
        settings.led_intensity = 255
        settings.reward_volume = 2
        settings.noise_time = 1.5
        settings.use_light = True

    def update_training_settings(self) -> None:
        pass


def _load(values: dict) -> TrainingProtocolBase:
    protocol = Protocol()
    protocol.copy_settings()
    protocol.load_settings_from_jsonstring(json.dumps(values))
    return protocol


def test_integer_settings_stay_integers():
    settings = _load({"led_intensity": 255, "reward_volume": 2}).settings
    assert settings.led_intensity == 255
    assert isinstance(settings.led_intensity, int)
    assert isinstance(settings.reward_volume, int)


def test_integer_settings_saved_as_floats_are_read_as_integers():
    # older versions saved every number as a float
    settings = _load({"led_intensity": 255.0, "reward_volume": "2.0"}).settings
    assert isinstance(settings.led_intensity, int)
    assert isinstance(settings.reward_volume, int)


def test_decimals_are_never_truncated():
    settings = _load({"reward_volume": "2.5"}).settings
    assert settings.reward_volume == 2.5


def test_float_settings_stay_floats():
    settings = _load({"noise_time": 3}).settings
    assert settings.noise_time == 3.0
    assert isinstance(settings.noise_time, float)


def test_text_from_the_gui():
    protocol = Protocol()
    protocol.copy_settings()
    wrong_keys = protocol.load_settings_from_dict(
        {"led_intensity": "128", "noise_time": "2", "use_light": "false"}
    )
    assert wrong_keys == []
    assert protocol.settings.led_intensity == 128
    assert isinstance(protocol.settings.led_intensity, int)
    assert isinstance(protocol.settings.noise_time, float)
    assert protocol.settings.use_light is False
