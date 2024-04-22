from enum import Enum


class State(Enum):
    WAIT = "all subjects at home, waiting for rfid detection"
    DETECTION = "subject detected, checking if it is allowed to enter"
    ACCESS = "access granted, launching the task"
    LAUNCH = (
        "task launched, waiting for the subject to perform the first action in the box"
    )
    ACTION = "subject performed the first action in the box, closing the door"
    CLOSE = "door closed, running the task, subject can not leave the box yet"
    OPEN = "task finished, opening the door"
    RUN_OPENED = "door opened, subject can leave the box"
    EXIT_UNSAVED = "subject leaving, task is not saved yet"
    WRAP_OUTSIDE = "task saved, subject is already outside"
    WRAP_INSIDE = "task saved, subject is still inside"
    EXIT_SAVED = "subject leaving, task is already saved"
    ERROR = "error occurred, disconnecting rfids and stopping the task"
    PREPARE = "manually preparing a task"
    MANUAL = "manually running a task"

    def __init__(self, description: str):
        self.description = description


class Subject:
    def __init__(self, name: str):
        self.name = name


class Task:
    def __init__(self, name: str):
        self.name = name


class AppState:
    def __init__(self):
        self.subject = Subject("None")
        self.task = Task("None")
        self.state = State.WAIT

        self.color_area1 = (128, 0, 128)
        self.color_area1_label = "color:rgb(128,0,128)"
        self.color_area2 = (165, 42, 42)
        self.color_area2_label = "color:rgb(165,42,42)"
        self.color_area3 = (0, 100, 0)
        self.color_area3_label = "color:rgb(0,100,0)"
        self.color_area4 = (122, 122, 122)
        self.color_area4_label = "color:rgb(128,0,128)"

        self.color_frame_number = (255, 0, 0)
        self.color_timestamp = (255, 0, 0)


app = AppState()
