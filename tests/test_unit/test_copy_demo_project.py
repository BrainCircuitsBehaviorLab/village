from pathlib import Path
from unittest.mock import patch

from village.classes.enums import Active
from village.scripts import utils


class FakeSettings:
    """Like the real settings: values are stored as given, and an Active
    setting is read back as the Active enum."""

    def __init__(self, code_directory: Path, copied: str = "OFF") -> None:
        self.values = {
            "DEFAULT_CODE_DIRECTORY": str(code_directory),
            "GITHUB_REPOSITORIES_DOWNLOADED": copied,
        }

    def get(self, key: str):
        if key == "GITHUB_REPOSITORIES_DOWNLOADED":
            return Active(self.values[key])
        return self.values[key]

    def set(self, key: str, value) -> None:
        self.values[key] = value


def _examples(tmp_path: Path) -> Path:
    source = tmp_path / "examples"
    (source / "arduino_firmware").mkdir(parents=True)
    (source / "task.py").write_text("# task")
    (source / "arduino_firmware" / "task.ino").write_text("// firmware")
    (source / "__pycache__").mkdir()
    (source / "__pycache__" / "task.cpython-311.pyc").write_text("")
    return source


def test_copies_examples_the_first_time(tmp_path):
    code = tmp_path / "demo" / "code"
    fake = FakeSettings(code)
    with (
        patch.object(utils, "settings", fake),
        patch.object(utils, "EXAMPLES_DIRECTORY", _examples(tmp_path)),
    ):
        utils.copy_demo_project()
    assert (code / "task.py").read_text() == "# task"
    assert (code / "arduino_firmware" / "task.ino").exists()
    assert not (code / "__pycache__").exists()
    assert fake.values["GITHUB_REPOSITORIES_DOWNLOADED"] == "ON"


def test_does_nothing_if_already_set_up(tmp_path):
    code = tmp_path / "demo" / "code"
    fake = FakeSettings(code, copied="ON")
    with (
        patch.object(utils, "settings", fake),
        patch.object(utils, "EXAMPLES_DIRECTORY", _examples(tmp_path)),
    ):
        utils.copy_demo_project()
    assert not code.exists()


def test_never_overwrites_existing_code(tmp_path):
    code = tmp_path / "demo" / "code"
    code.mkdir(parents=True)
    (code / "task.py").write_text("# my own version")
    fake = FakeSettings(code)
    with (
        patch.object(utils, "settings", fake),
        patch.object(utils, "EXAMPLES_DIRECTORY", _examples(tmp_path)),
    ):
        utils.copy_demo_project()
    assert (code / "task.py").read_text() == "# my own version"
    assert fake.values["GITHUB_REPOSITORIES_DOWNLOADED"] == "ON"


def test_falls_back_to_empty_project_if_copy_fails(tmp_path):
    code = tmp_path / "demo" / "code"
    fake = FakeSettings(code)
    with (
        patch.object(utils, "settings", fake),
        patch.object(utils, "EXAMPLES_DIRECTORY", tmp_path / "missing"),
        patch.object(utils, "change_directory_settings") as change,
        patch.object(utils, "log"),
    ):
        utils.copy_demo_project()
    assert change.call_args.kwargs["new_path"].endswith("empty-project")
    assert fake.values["GITHUB_REPOSITORIES_DOWNLOADED"] == "OFF"
