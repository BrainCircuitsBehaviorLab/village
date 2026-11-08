import sys
from unittest.mock import MagicMock

import pandas as pd

sys.modules.setdefault("fire", MagicMock())

from village.scripts.global_csv_for_subject import main  # noqa: E402


def _write_session(directory, filename):
    (directory / (filename + ".csv")).write_text(
        "date;trial;subject;task;system_name\n" + filename + ";1;C_3;x;village01\n"
    )
    (directory / (filename + "_RAW.csv")).write_text("TRIAL;START\n")


def test_sessions_sorted_by_date_with_underscores_in_names(tmp_path):
    subject_directory = tmp_path / "C_3"
    subject_directory.mkdir()
    for filename in [
        "C_3_S4_1_20261107_222055",
        "C_3_Bpod1Habituation_20261105_090000",
        "C_3_S4_1_20261106_120000",
        "C_3_S4_5_third_condition_20261108_080000",
    ]:
        _write_session(subject_directory, filename)
    (subject_directory / "notes.csv").write_text("not a session\n")

    main("C_3", str(tmp_path), deleted_sessions=["C_3_S4_1_20261106_120000.csv"])

    df = pd.read_csv(subject_directory / "C_3.csv", sep=";")
    assert df["session"].tolist() == [1, 2, 3]
    assert df["date"].tolist() == [
        "C_3_Bpod1Habituation_20261105_090000",
        "C_3_S4_1_20261107_222055",
        "C_3_S4_5_third_condition_20261108_080000",
    ]
