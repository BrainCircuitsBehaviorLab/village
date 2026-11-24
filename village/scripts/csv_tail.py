"""Incremental reading of a CSV file that keeps growing."""

import io
from pathlib import Path

import pandas as pd


class CsvTail:
    """Reads a CSV file that keeps growing, reading only the lines added since
    the previous read.

    Used for session.csv, which is written during the whole session and shown
    in DATA, refreshed every second: reading it whole every time would cost
    more and more as the session goes on.

    The values are read as text, as they are in the file. The file is read
    again from the beginning when it gets smaller (a new session rewrites it).
    An incomplete last line is left for the next read.
    """

    def __init__(self, path: str | Path, sep: str = ";") -> None:
        self.path = Path(path)
        self.sep = sep
        self.reset()

    def reset(self) -> None:
        """Forgets what was read: the next read starts from the beginning."""
        self.offset = 0
        self.header = ""
        self.df = pd.DataFrame()

    def read(self) -> pd.DataFrame:
        """Reads the new lines and returns all the data read so far.

        Returns:
            pd.DataFrame: The data, or an empty DataFrame if the file cannot be
            read.
        """
        try:
            size = self.path.stat().st_size
            if size < self.offset:
                self.reset()
            if size == self.offset:
                return self.df
            with self.path.open("rb") as file:
                file.seek(self.offset)
                chunk = file.read(size - self.offset)
            end = chunk.rfind(b"\n") + 1
            if end == 0:
                return self.df
            self.offset += end
            text = chunk[:end].decode("utf-8", errors="replace")
            if not self.header:
                self.header, _, text = text.partition("\n")
            if text:
                new_rows = pd.read_csv(
                    io.StringIO(self.header + "\n" + text),
                    sep=self.sep,
                    dtype=str,
                    keep_default_na=False,
                )
                if self.df.empty:
                    self.df = new_rows
                else:
                    self.df = pd.concat([self.df, new_rows], ignore_index=True)
            elif self.df.empty:
                self.df = pd.DataFrame(columns=self.header.split(self.sep))
        except Exception:
            self.reset()
        return self.df
