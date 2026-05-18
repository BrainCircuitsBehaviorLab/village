import datetime

from village.classes.collection import convert_active
from village.scripts.time_utils import time_utils

# ── convert_active ───────────────────────────────────────────────────────────


class TestConvertActive:
    # ON variants
    def test_on_uppercase(self):
        assert convert_active("ON") == "ON"

    def test_on_lowercase(self):
        assert convert_active("on") == "ON"

    def test_on_mixed(self):
        assert convert_active("On") == "ON"

    # OFF variants
    def test_off_uppercase(self):
        assert convert_active("OFF") == "OFF"

    def test_off_lowercase(self):
        assert convert_active("off") == "OFF"

    def test_off_mixed(self):
        assert convert_active("Off") == "OFF"

    # Empty / whitespace → default ON (new subject)
    def test_empty_returns_on(self):
        assert convert_active("") == "ON"

    def test_whitespace_returns_on(self):
        assert convert_active("   ") == "ON"

    # New pipe format: passed through unchanged
    def test_pipe_format_passthrough(self):
        assert convert_active("Mon|Tue:8-17") == "Mon|Tue:8-17"

    def test_pipe_all_days_passthrough(self):
        value = "Mon|Tue|Wed|Thu|Fri|Sat|Sun"
        assert convert_active(value) == value

    # Legacy hyphen-separated day format
    def test_legacy_single_day(self):
        assert convert_active("Mon") == "Mon"

    def test_legacy_multiple_days(self):
        assert convert_active("Mon-Wed-Fri") == "Mon-Wed-Fri"

    def test_legacy_all_days(self):
        assert convert_active("Mon-Tue-Wed-Thu-Fri-Sat-Sun") == (
            "Mon-Tue-Wed-Thu-Fri-Sat-Sun"
        )

    # Invalid → OFF
    def test_invalid_string(self):
        assert convert_active("invalid") == "OFF"

    def test_partial_valid_day(self):
        assert convert_active("Mon-INVALID-Fri") == "OFF"

    def test_numeric_only(self):
        assert convert_active("123") == "OFF"

    # Whitespace trimming
    def test_strips_leading_trailing_spaces(self):
        assert convert_active("  ON  ") == "ON"


# ── time_utils.range_24_hours ────────────────────────────────────────────────


class TestRange24Hours:
    def _date(self, dt_str: str) -> datetime.datetime:
        return datetime.datetime.fromisoformat(dt_str)

    def test_duration_is_exactly_24h(self):
        start, end = time_utils.range_24_hours(
            self._date("2025-01-07 08:00:00"),
            datetime.time(8, 0),
        )
        assert end - start == datetime.timedelta(hours=24)

    def test_start_matches_init_time(self):
        day = self._date("2025-01-07 15:00:00")
        start, _ = time_utils.range_24_hours(day, datetime.time(8, 0))
        assert start == datetime.datetime(2025, 1, 7, 8, 0, 0)

    def test_end_is_next_day(self):
        day = self._date("2025-01-07 00:00:00")
        _, end = time_utils.range_24_hours(day, datetime.time(6, 0))
        assert end == datetime.datetime(2025, 1, 8, 6, 0, 0)

    def test_midnight_init_time(self):
        day = self._date("2025-01-07 00:00:00")
        start, end = time_utils.range_24_hours(day, datetime.time(0, 0))
        assert start == datetime.datetime(2025, 1, 7, 0, 0, 0)
        assert end == datetime.datetime(2025, 1, 8, 0, 0, 0)

    def test_point_inside_range(self):
        day = self._date("2025-01-07 00:00:00")
        start, end = time_utils.range_24_hours(day, datetime.time(8, 0))
        point = datetime.datetime(2025, 1, 7, 14, 0, 0)
        assert start <= point <= end

    def test_point_outside_range(self):
        day = self._date("2025-01-07 00:00:00")
        start, end = time_utils.range_24_hours(day, datetime.time(8, 0))
        before = datetime.datetime(2025, 1, 7, 7, 59, 0)
        assert not (start <= before <= end)
