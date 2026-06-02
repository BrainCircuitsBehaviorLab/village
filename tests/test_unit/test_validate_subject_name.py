import pytest

from village.scripts.utils import validate_subject_name


def ok(name: str) -> None:
    assert validate_subject_name(name) is None


def err(name: str) -> None:
    assert validate_subject_name(name) is not None


# ── valid names ──────────────────────────────────────────────────────────────


def test_letters_only():
    ok("MouseA")


def test_letters_and_numbers():
    ok("Mouse01")


def test_underscore():
    ok("mouse_01")


def test_hyphen():
    ok("mouse-01")


def test_mixed():
    ok("AB_c-123")


def test_single_letter():
    ok("A")


def test_single_digit():
    ok("1")


def test_purely_numeric():
    # Current behaviour: purely numeric names ARE allowed.
    # Risk: if the subjects CSV is read without explicit dtype=str,
    # pandas will parse "123" as integer 123.
    # Within this system it is safe (dtype is forced to str), but
    # be aware when exporting or opening the CSV externally.
    ok("123")


def test_long_valid_name():
    ok("A" * 50)


# ── invalid names ────────────────────────────────────────────────────────────


def test_empty_string():
    err("")


def test_whitespace_only():
    err("   ")


def test_space_inside():
    err("Mouse A")


def test_dot():
    err("mouse.1")


def test_at_sign():
    err("mouse@lab")


def test_slash():
    err("mouse/1")


def test_backslash():
    err("mouse\\1")


def test_parenthesis():
    err("mouse(1)")


def test_unicode_letter():
    err("ratón")


def test_newline():
    err("mouse\n1")


def test_tab():
    err("mouse\t1")


# ── Windows reserved names ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "name",
    [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM9",
        "LPT1",
        "LPT9",
    ],
)
def test_reserved_uppercase(name):
    err(name)


@pytest.mark.parametrize("name", ["con", "prn", "aux", "nul", "com1", "lpt1"])
def test_reserved_lowercase(name):
    err(name)


@pytest.mark.parametrize("name", ["Con", "Prn", "Com1", "Lpt1"])
def test_reserved_mixed_case(name):
    err(name)
