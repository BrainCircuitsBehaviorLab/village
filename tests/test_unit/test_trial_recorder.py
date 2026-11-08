import pytest

from village.controllers import trial_recorder
from village.controllers.trial_recorder import TrialRecorder


@pytest.fixture
def recorder(tmp_path, monkeypatch):
    monkeypatch.setattr(
        trial_recorder.settings, "get", lambda key: str(tmp_path), raising=False
    )
    rec = TrialRecorder()
    yield rec
    rec.close()


def test_state_names_containing_start(recorder):
    # The Raspberry Pi is the controller: the same clock for both timestamps
    recorder.start_trial(100.0, 100.0)
    recorder.enter_state("START_poke", 100.0)
    recorder.enter_state("wait", 101.0)
    recorder.end_trial(103.0)
    data = recorder.get_trial_data("2026-11-08 10:00:00", 1, "mouse1", "Task", "v01")

    assert data["STATE_START_poke_START"] == [100.0]
    assert data["STATE_START_poke_END"] == [101.0]
    assert data["STATE_wait_START"] == [101.0]
    assert data["STATE_wait_END"] == [103.0]
    assert "STATE_END_poke_END" not in data
