from PyQt5.QtWidgets import QWidget


class PyBpodProtocol:
    def create_state_machine(self) -> None:
        return

    def send_and_run_state_machine(self) -> None:
        return


class LogProtocol:
    def log(self, date: str, type: str, subject: str, description: str) -> None:
        return


class CameraProtocol:
    area1: list[int]
    area2: list[int]
    area3: list[int]
    area4: list[int]
    areas: list[list[int]]
    change: bool

    def start_camera(self) -> None:
        return

    def stop_preview(self) -> None:
        return

    def stop_window_preview(self) -> None:
        return

    def start_record(self) -> None:
        return

    def stop_record(self) -> None:
        return

    def stop(self) -> None:
        return

    def change_focus(self, lensposition) -> None:
        return

    def change_framerate(self, framerate) -> None:
        return

    def print_info_about_config(self) -> None:
        return

    def pre_process(self, request) -> None:
        return

    def start_preview_window(self) -> QWidget:
        return QWidget()
