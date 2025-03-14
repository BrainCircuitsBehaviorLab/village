import os

import fire
import pandas as pd


def main(
    subject: str, sessions_directory: str, deleted_sessions: list[str] = []
) -> None:
    subject_directory = os.path.join(sessions_directory, subject)
    final_name = subject + ".csv"
    final_path = os.path.join(sessions_directory, subject, final_name)

    sessions = []
    for file in os.listdir(subject_directory):
        if file in deleted_sessions:
            continue
        if file.endswith("_RAW.csv"):
            continue
        if file == final_name:
            continue
        elif file.endswith(".csv"):
            sessions.append(file)

    def extract_datetime(filename) -> str:
        base_name = str(os.path.basename(filename))
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

    sorted_sessions = [
        os.path.join(subject_directory, session) for session in sorted_sessions
    ]

    dfs: list[pd.DataFrame] = []

    for i, session in enumerate(sorted_sessions):
        df = pd.read_csv(session, sep=";")
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
