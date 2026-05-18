import datetime

import pytest

from village.scripts.time_utils import time_utils

# ── format_duration ──────────────────────────────────────────────────────────


class TestFormatDuration:
    def test_zero(self):
        assert time_utils.format_duration(0) == "00:00:00.000"

    def test_one_millisecond(self):
        assert time_utils.format_duration(1) == "00:00:00.001"

    def test_one_second(self):
        assert time_utils.format_duration(1_000) == "00:00:01.000"

    def test_one_minute(self):
        assert time_utils.format_duration(60_000) == "00:01:00.000"

    def test_one_hour(self):
        assert time_utils.format_duration(3_600_000) == "01:00:00.000"

    def test_mixed(self):
        ms = 2 * 3_600_000 + 3 * 60_000 + 4 * 1_000 + 567
        assert time_utils.format_duration(ms) == "02:03:04.567"

    def test_more_than_24_hours(self):
        ms = 25 * 3_600_000
        assert time_utils.format_duration(ms) == "25:00:00.000"

    def test_999_milliseconds(self):
        assert time_utils.format_duration(999) == "00:00:00.999"


# ── time_from_setting_string ─────────────────────────────────────────────────


class TestTimeFromSettingString:
    def test_valid(self):
        assert time_utils.time_from_setting_string("08:30") == datetime.time(8, 30)

    def test_midnight(self):
        assert time_utils.time_from_setting_string("00:00") == datetime.time(0, 0)

    def test_23_59(self):
        assert time_utils.time_from_setting_string("23:59") == datetime.time(23, 59)

    def test_invalid_defaults_to_08(self):
        assert time_utils.time_from_setting_string("not-a-time") == datetime.time(8, 0)

    def test_empty_defaults_to_08(self):
        assert time_utils.time_from_setting_string("") == datetime.time(8, 0)

    def test_none_defaults_to_08(self):
        assert time_utils.time_from_setting_string(None) == datetime.time(8, 0)


# ── date_from_string / string_from_date ──────────────────────────────────────


class TestDateStringRoundtrip:
    def test_roundtrip(self):
        dt = datetime.datetime(2025, 3, 15, 10, 30, 0)
        assert time_utils.date_from_string(time_utils.string_from_date(dt)) == dt

    def test_string_format(self):
        dt = datetime.datetime(2025, 1, 7, 8, 0, 0)
        assert time_utils.string_from_date(dt) == "2025-01-07 08:00:00"

    def test_parse_known_string(self):
        result = time_utils.date_from_string("2025-01-07 10:30:00")
        assert result == datetime.datetime(2025, 1, 7, 10, 30, 0)

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError):
            time_utils.date_from_string("not-a-date")


# ── date_from_path ───────────────────────────────────────────────────────────


class TestDateFromPath:
    def test_standard_path(self):
        path = "/data/sessions/subject_20250107_103045.csv"
        result = time_utils.date_from_path(path)
        assert result == datetime.datetime(2025, 1, 7, 10, 30, 45)

    def test_filename_only(self):
        result = time_utils.date_from_path("video_20241231_235959.mp4")
        assert result == datetime.datetime(2024, 12, 31, 23, 59, 59)

    def test_invalid_path_raises(self):
        with pytest.raises((ValueError, IndexError)):
            time_utils.date_from_path("no_date_here.csv")
