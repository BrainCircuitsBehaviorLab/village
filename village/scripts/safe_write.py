import os
from pathlib import Path
from typing import Any

import pandas as pd


def write_csv_atomic(df: pd.DataFrame, path: str | Path, **kwargs: Any) -> None:
    """Writes df to path as a CSV, replacing the previous file in one step.

    The CSV is first written to a temporary file next to path and flushed to
    disk, and then renamed to path. A rename is atomic, so if the system stops
    in the middle (a power cut), path keeps its previous content instead of a
    half-written file.

    Args:
        df (pd.DataFrame): The data to write.
        path (str | Path): The CSV file to replace.
        **kwargs: Passed to DataFrame.to_csv (sep, index, header...).
    """
    path = Path(path)
    tmp_path = path.with_name(path.name + ".tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as f:
        df.to_csv(f, **kwargs)
        f.flush()
        os.fsync(f.fileno())
    tmp_path.replace(path)
