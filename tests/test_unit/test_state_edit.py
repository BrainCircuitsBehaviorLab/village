"""Tests for the states in which the tables can be edited."""

from village.classes.enums import State


def test_can_edit_data_only_in_wait() -> None:
    """Editing starts only from WAIT: never during a session or another edit."""
    allowed = [state for state in State if state.can_edit_data()]
    assert allowed == [State.WAIT]
