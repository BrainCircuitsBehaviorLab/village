from unittest.mock import patch

import pandas as pd
import pytest

from village.scripts.safe_write import write_csv_atomic


def test_writes_the_csv(tmp_path):
    path = tmp_path / "subjects.csv"
    df = pd.DataFrame({"name": ["mouse1", "mouse2"], "weight": [20.1, 21.3]})
    write_csv_atomic(df, path, index=False, sep=";")
    assert path.read_text() == "name;weight\nmouse1;20.1\nmouse2;21.3\n"
    assert not (tmp_path / "subjects.csv.tmp").exists()


def test_replaces_the_previous_file(tmp_path):
    path = tmp_path / "subjects.csv"
    path.write_text("old content\n")
    write_csv_atomic(pd.DataFrame({"a": [1]}), path, index=False, sep=";")
    assert path.read_text() == "a\n1\n"


def test_failed_write_keeps_the_previous_file(tmp_path):
    path = tmp_path / "subjects.csv"
    path.write_text("old content\n")
    with (
        patch.object(pd.DataFrame, "to_csv", side_effect=OSError("disk full")),
        pytest.raises(OSError),
    ):
        write_csv_atomic(pd.DataFrame({"a": [1]}), path, index=False, sep=";")
    assert path.read_text() == "old content\n"
