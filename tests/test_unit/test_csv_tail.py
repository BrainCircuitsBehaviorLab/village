"""Tests for the incremental reading of a growing CSV file (CsvTail)."""

from pathlib import Path

from village.scripts.csv_tail import CsvTail

HEADER = "TRIAL;START;END;MSG;VALUE\n"


def test_reads_only_the_new_lines(tmp_path: Path) -> None:
    path = tmp_path / "session.csv"
    path.write_text(HEADER + "1;0.1;0.2;STATE_A;\n")
    tail = CsvTail(path)
    assert tail.read()["MSG"].tolist() == ["STATE_A"]
    with path.open("a") as file:
        file.write("1;0.2;0.3;STATE_B;5\n")
    df = tail.read()
    assert df["MSG"].tolist() == ["STATE_A", "STATE_B"]
    assert df["VALUE"].tolist() == ["", "5"]  # as text, as in the file


def test_incomplete_line_waits_for_the_next_read(tmp_path: Path) -> None:
    path = tmp_path / "session.csv"
    path.write_text(HEADER + "1;0.1;0.2;STATE_A;\n1;0.2;0.3;STA")
    tail = CsvTail(path)
    assert tail.read()["MSG"].tolist() == ["STATE_A"]
    with path.open("a") as file:
        file.write("TE_B;\n")
    assert tail.read()["MSG"].tolist() == ["STATE_A", "STATE_B"]


def test_only_header_gives_the_columns(tmp_path: Path) -> None:
    path = tmp_path / "session.csv"
    path.write_text(HEADER)
    df = CsvTail(path).read()
    assert df.empty
    assert df.columns.tolist() == ["TRIAL", "START", "END", "MSG", "VALUE"]


def test_rewritten_file_is_read_again(tmp_path: Path) -> None:
    """A new session rewrites the file: it is read from the beginning."""
    path = tmp_path / "session.csv"
    path.write_text(HEADER + "1;0.1;0.2;OLD_A;\n1;0.2;0.3;OLD_B;\n")
    tail = CsvTail(path)
    assert len(tail.read()) == 2
    path.write_text(HEADER + "1;0.1;0.2;NEW;\n")
    assert tail.read()["MSG"].tolist() == ["NEW"]


def test_missing_file_gives_an_empty_table(tmp_path: Path) -> None:
    tail = CsvTail(tmp_path / "missing.csv")
    assert tail.read().empty
    assert tail.offset == 0
