"""Tests for the edits of a collection applied on its current data
(Collection.replace_row and Collection.update_where)."""

from pathlib import Path

import pandas as pd

from village.classes.collection import Collection

COLUMNS = ["date", "subject", "weight", "trials"]
TYPES = [str, str, float, int]


def make_collection(tmp_path: Path, rows: list[list]) -> Collection:
    """A collection saved in tmp_path, without reading the settings."""
    collection = Collection()
    collection.name = "test"
    collection.columns = COLUMNS
    collection.types = TYPES
    collection.dict = dict(zip(COLUMNS, TYPES, strict=False))
    collection.path = tmp_path / "test.csv"
    collection._df = collection.convert_df_to_types(pd.DataFrame(rows, columns=COLUMNS))
    return collection


def row(collection: Collection, position: int) -> pd.Series:
    """A row as the GUI takes it, from a copy of the data."""
    df = collection.df
    return pd.Series(
        {col: df.iat[position, i] for i, col in enumerate(df.columns)}, dtype=object
    )


def saved(collection: Collection) -> pd.DataFrame:
    return pd.read_csv(collection.path, sep=";")


def test_edit_keeps_rows_added_in_the_meantime(tmp_path: Path) -> None:
    """An edit made on an old copy does not delete the rows added since."""
    collection = make_collection(tmp_path, [["d1", "A", 20.0, 10]])
    old = row(collection, 0)  # the GUI copy
    collection._df = pd.concat(  # a session ends and adds its row
        [collection._df, pd.DataFrame([["d2", "B", 21.0, 5]], columns=COLUMNS)],
        ignore_index=True,
    )
    new = old.copy()
    new["weight"] = 25.0
    assert collection.replace_row(old, new) == ""
    assert collection.df["weight"].tolist() == [25.0, 21.0]
    assert saved(collection)["subject"].tolist() == ["A", "B"]


def test_edit_of_a_row_changed_in_the_meantime_is_refused(tmp_path: Path) -> None:
    """Nothing is overwritten if the row changed after the GUI copy."""
    collection = make_collection(tmp_path, [["d1", "A", 20.0, 10]])
    old = row(collection, 0)
    new = old.copy()
    new["weight"] = 25.0
    collection._df.loc[0, "trials"] = 99  # changed after the GUI copy
    reason = collection.replace_row(old, new)
    assert reason == "The row was changed or deleted in the meantime."
    assert collection.df["trials"].tolist() == [99]


def test_delete_finds_the_row_by_content(tmp_path: Path) -> None:
    rows = [["d1", "A", 20.0, 10], ["d2", "B", 21.0, 5], ["d3", "C", 22.0, 7]]
    collection = make_collection(tmp_path, rows)
    old = row(collection, 1)
    collection._df = collection._df.drop(0).reset_index(drop=True)  # shifted
    assert collection.replace_row(old, None) == ""
    assert collection.df["subject"].tolist() == ["C"]


def test_add_row(tmp_path: Path) -> None:
    collection = make_collection(tmp_path, [["d1", "A", 20.0, 10]])
    empty = pd.Series("", index=COLUMNS, dtype=object)
    assert collection.replace_row(None, empty) == ""
    df = collection.df
    assert len(df) == 2
    assert df.iloc[1].tolist() == ["", "", 0.0, 0]


def test_check_can_refuse_the_change(tmp_path: Path) -> None:
    collection = make_collection(tmp_path, [["d1", "A", 20.0, 10]])
    old = row(collection, 0)
    reason = collection.replace_row(old, None, check=lambda: "Not now.")
    assert reason == "Not now."
    assert len(collection.df) == 1
    assert not collection.path.exists()


def test_int_columns_are_found(tmp_path: Path) -> None:
    """Rows of tables with only numeric columns are found too."""
    collection = make_collection(tmp_path, [["d1", "A", 20.0, 10]])
    collection.columns = ["weight", "trials"]
    collection.types = [float, int]
    collection._df = collection._df[["weight", "trials"]]
    old = row(collection, 0)
    assert collection.replace_row(old, None) == ""
    assert len(collection.df) == 0


def test_update_where(tmp_path: Path) -> None:
    rows = [["d1", "A", 20.0, 10], ["d2", "B", 21.0, 5]]
    collection = make_collection(tmp_path, rows)
    collection.update_where({"subject": "B"}, {"trials": 8, "date": "d9"})
    assert collection.df["trials"].tolist() == [10, 8]
    assert saved(collection)["date"].tolist() == ["d1", "d9"]


def test_update_where_several_columns(tmp_path: Path) -> None:
    """The weight goes to the row of that date and subject, not the last one."""
    rows = [["d1", "A", 20.0, 10], ["d1", "B", 21.0, 5], ["d2", "C", 22.0, 7]]
    collection = make_collection(tmp_path, rows)
    collection.update_where({"date": "d1", "subject": "B"}, {"weight": 30.0})
    assert collection.df["weight"].tolist() == [20.0, 30.0, 22.0]


def test_update_where_without_matches_changes_nothing(tmp_path: Path) -> None:
    collection = make_collection(tmp_path, [["d1", "A", 20.0, 10]])
    collection.update_where({"date": "d9", "subject": "A"}, {"weight": 30.0})
    assert collection.df["weight"].tolist() == [20.0]
