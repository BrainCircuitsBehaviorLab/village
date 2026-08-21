from pathlib import Path

import fire
import pandas as pd


def main(
    subject: str, sessions_directory: str, deleted_sessions: list[str] | None = None
) -> None:
    """Consolidates individual session CSVs for a subject into a single global CSV.

    Args:
        subject (str): The name of the subject.
        sessions_directory (str): The directory containing session data.
        deleted_sessions (list[str]): List of session filenames to exclude.
    """
    if deleted_sessions is None:
        deleted_sessions = []
    subject_directory = Path(sessions_directory, subject)
    final_name = subject + ".csv"
    final_path = subject_directory / final_name

    sessions = []
    for entry in subject_directory.iterdir():
        file = entry.name
        if file in deleted_sessions:
            continue
        if file.endswith("_RAW.csv"):
            continue
        if file == final_name:
            continue
        elif file.endswith(".csv"):
            sessions.append(file)

    def extract_datetime(filename) -> str:
        """Extracts the datetime timestamp from a session filename.

        Args:
            filename (str): The session filename.

        Returns:
            str: The extracted timestamp string.
        """
        base_name = Path(filename).name
        datetime = base_name.split("_")[2] + base_name.split("_")[3].split(".")[0]
        return datetime

    sessions_datetimes = []

    for session in sessions:
        try:
            datetime = extract_datetime(session)
            sessions_datetimes.append((session, datetime))
        except Exception:
            pass

    sorted_sessions = [
        session for session, _ in sorted(sessions_datetimes, key=lambda x: x[1])
    ]

    sorted_session_paths = [subject_directory / session for session in sorted_sessions]

    dfs: list[pd.DataFrame] = []

    for i, session_path in enumerate(sorted_session_paths):
        df = pd.read_csv(session_path, sep=";")
        df.insert(loc=0, column="session", value=i + 1)
        dfs.append(df)

    final_df = pd.concat(dfs)

    priority_columns = [
        "session",
        "date",
        "trial",
        "subject",
        "task",
        "system_name",
    ]
    reordered_columns = priority_columns + [
        col for col in final_df.columns if col not in priority_columns
    ]
    final_df = final_df[reordered_columns]

    final_df.to_csv(final_path, header=True, index=False, sep=";")


if __name__ == "__main__":
    fire.Fire(main)
