from datetime import datetime
from unittest.mock import patch

from village.scripts import utils


def _dt(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str)


# ── _hours_spec_to_set ───────────────────────────────────────────────────────


def test_spec_to_set_single_range():
    assert utils._hours_spec_to_set("8-11") == frozenset({8, 9, 10, 11})


def test_spec_to_set_multiple_ranges():
    result = utils._hours_spec_to_set("8-11,16-18")
    assert result == frozenset({8, 9, 10, 11, 16, 17, 18})


def test_spec_to_set_single_hour():
    assert utils._hours_spec_to_set("5") == frozenset({5})


def test_spec_to_set_full_day():
    assert utils._hours_spec_to_set("0-23") == utils._ALL_HOURS


# ── _hours_set_to_spec ───────────────────────────────────────────────────────


def test_set_to_spec_all_hours_returns_none():
    assert utils._hours_set_to_spec(utils._ALL_HOURS) is None


def test_set_to_spec_single_range():
    assert utils._hours_set_to_spec(frozenset({8, 9, 10, 11})) == "8-11"


def test_set_to_spec_multiple_ranges():
    result = utils._hours_set_to_spec(frozenset({8, 9, 10, 11, 16, 17, 18}))
    assert result == "8-11,16-18"


def test_set_to_spec_single_hour():
    assert utils._hours_set_to_spec(frozenset({5})) == "5"


def test_set_to_spec_roundtrip():
    original = frozenset({8, 9, 10, 11, 16, 17, 18, 19, 20, 21, 22, 23})
    spec = utils._hours_set_to_spec(original)
    assert utils._hours_spec_to_set(spec) == original


# ── _parse_schedule ──────────────────────────────────────────────────────────


def test_parse_single_day_all_hours():
    assert utils._parse_schedule("Mon") == {"Mon": utils._ALL_HOURS}


def test_parse_multiple_days_all_hours():
    result = utils._parse_schedule("Mon|Wed|Fri")
    assert result == {
        "Mon": utils._ALL_HOURS,
        "Wed": utils._ALL_HOURS,
        "Fri": utils._ALL_HOURS,
    }


def test_parse_day_with_hour_range():
    result = utils._parse_schedule("Tue:8-11,16-23")
    assert result == {"Tue": frozenset(range(8, 12)) | frozenset(range(16, 24))}


def test_parse_mixed():
    result = utils._parse_schedule("Mon|Tue:8-11|Wed")
    assert result["Mon"] == utils._ALL_HOURS
    assert result["Tue"] == frozenset({8, 9, 10, 11})
    assert result["Wed"] == utils._ALL_HOURS


def test_parse_legacy_format():
    result = utils._parse_schedule("Mon-Wed-Fri")
    assert result == {
        "Mon": utils._ALL_HOURS,
        "Wed": utils._ALL_HOURS,
        "Fri": utils._ALL_HOURS,
    }


def test_parse_unknown_token_ignored():
    result = utils._parse_schedule("Mon|INVALID|Fri")
    assert "INVALID" not in result
    assert "Mon" in result
    assert "Fri" in result


# ── is_active ────────────────────────────────────────────────────────────────


def test_is_active_on():
    assert utils.is_active("ON") is True


def test_is_active_off():
    assert utils.is_active("OFF") is False


def test_is_active_today_in_schedule():
    # Tuesday 10:00 → hour 10 is in all-hours schedule for Tuesday
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 10:00:00")
        assert utils.is_active("Tue") is True


def test_is_active_wrong_day():
    # Tuesday → Monday not active
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 10:00:00")
        assert utils.is_active("Mon|Wed") is False


def test_is_active_hour_in_range():
    # Tuesday 12:00, hours 8-17 active → True
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 12:00:00")
        assert utils.is_active("Tue:8-17") is True


def test_is_active_hour_outside_range():
    # Tuesday 18:00, hours 8-17 active → False
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 18:00:00")
        assert utils.is_active("Tue:8-17") is False


def test_is_active_boundary_start():
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 08:00:00")
        assert utils.is_active("Tue:8-17") is True


def test_is_active_boundary_end():
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 17:00:00")
        assert utils.is_active("Tue:8-17") is True


def test_is_active_legacy_format():
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 10:00:00")  # Tuesday
        assert utils.is_active("Mon-Tue-Wed") is True


# ── active_last_24_hours ─────────────────────────────────────────────────────


def test_active_last_24_on():
    assert utils.active_last_24_hours("ON") is True


def test_active_last_24_off():
    assert utils.active_last_24_hours("OFF") is False


def test_active_last_24_both_days_all_hours():
    # Tuesday 10:00 — Mon and Tue all hours → True
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 10:00:00")
        assert utils.active_last_24_hours("Mon|Tue") is True


def test_active_last_24_only_today():
    # Only Tuesday → Monday hours not covered → False
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 10:00:00")
        assert utils.active_last_24_hours("Tue") is False


def test_active_last_24_only_yesterday():
    # Only Monday → Tuesday hours not covered → False
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 10:00:00")
        assert utils.active_last_24_hours("Mon") is False


def test_active_last_24_all_days():
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 10:00:00")
        assert utils.active_last_24_hours("Mon|Tue|Wed|Thu|Fri|Sat|Sun") is True


def test_active_last_24_partial_hours_gap():
    # Mon 8-17 and Tue 8-17: hours outside 8-17 are not covered → False
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-07 10:00:00")
        assert utils.active_last_24_hours("Mon:8-17|Tue:8-17") is False


def test_active_last_24_weekend_wraparound():
    # Monday 10:00 — yesterday is Sunday
    with patch("village.scripts.utils.time_utils") as mock_tu:
        mock_tu.now.return_value = _dt("2025-01-06 10:00:00")  # Monday
        assert utils.active_last_24_hours("Sun|Mon") is True
