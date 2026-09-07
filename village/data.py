from village.classes.collection import Collection


class Data:
    """Access point for the project's CSV-backed data collections, kept
    independent of Manager so any project code (tasks, plots, direct
    functions...) can do `from village.data import data` and read
    `data.sessions_summary.df`/`data.events.df`/etc. from anywhere, without
    pulling in the Bpod/camera/GUI machinery that importing village.manager
    drags along.

    The collections aren't actually usable until load() has run -- it
    needs SYSTEM_DIRECTORY to already point at a real, existing directory,
    so Manager calls it once during its own startup, before anything else
    in the project runs. In practice this is always ready by the time your
    own code executes.
    """

    def __init__(self) -> None:
        self.events = Collection()
        self.sessions_summary = Collection()
        self.subjects = Collection()
        self.temperatures = Collection()
        self.deleted_sessions = Collection()

    def load(self) -> None:
        """Reads (or creates) the backing CSVs. Called once by Manager."""
        self.events.create_data_collection(
            "events.csv",
            ["date", "type", "subject", "description"],
            [str, str, str, str],
        )
        self.sessions_summary.create_data_collection(
            "sessions_summary.csv",
            [
                "date",
                "subject",
                "tag",
                "weight",
                "task",
                "duration",
                "trials",
                "water",
                "settings",
            ],
            [str, str, str, float, str, float, int, float, str],
        )
        self.subjects.create_data_collection(
            "subjects.csv",
            [
                "name",
                "tag",
                "basal_weight",
                "active",
                "next_session_time",
                "next_settings",
            ],
            [str, str, float, str, str, str],
        )
        self.temperatures.create_data_collection(
            "temperatures.csv",
            ["date", "temperature", "humidity"],
            [str, float, float],
        )
        self.deleted_sessions.create_data_collection(
            "deleted_sessions.csv",
            ["filename"],
            [str],
        )


data = Data()
