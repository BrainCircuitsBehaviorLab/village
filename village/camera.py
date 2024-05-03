import os
import time
from pprint import pprint
from typing import Any, Protocol

import cv2

try:
    from libcamera import controls
    from picamera2 import MappedArray, Picamera2, Preview
    from picamera2.encoders import H264Encoder, Quality
    from picamera2.outputs import FfmpegOutput
    from picamera2.previews.qt import QGlPicamera2  # type: ignore
except Exception:
    pass

from PyQt5.QtWidgets import QWidget

from village.app_state import app
from village.log import log
from village.settings import settings

# info about picamera2: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf

# configure the logging of libcamera (the C++ library picamera2 uses)
os.environ["LIBCAMERA_LOG_LEVELS"] = "2"
# '0' = DEBUG, '1' = INFO, '2' = WARNING, '3' = ERROR, '4' = FATAL


# use this function to get info
def print_info_about_the_connected_cameras() -> None:
    print("INFO ABOUT THE CONNECTED CAMERAS:")
    pprint(Picamera2.global_camera_info())
    print()


class CameraProtocol(Protocol):
    area1: tuple[int, int, int, int]
    area2: tuple[int, int, int, int]
    area3: tuple[int, int, int, int]
    area4: tuple[int, int, int, int]

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


class NullCamera(CameraProtocol):
    area1: tuple[int, int, int, int]
    area2: tuple[int, int, int, int]
    area3: tuple[int, int, int, int]
    area4: tuple[int, int, int, int]

    def start_camera(self) -> None:
        pass

    def stop_preview(self) -> None:
        pass

    def stop_window_preview(self) -> None:
        pass

    def start_record(self) -> None:
        pass

    def stop_record(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def change_focus(self, lensposition) -> None:
        pass

    def change_framerate(self, framerate) -> None:
        pass

    def print_info_about_config(self) -> None:
        pass

    def pre_process(self, request) -> None:
        pass

    def start_preview_window(self) -> QWidget:
        return QWidget()


# the camera class
class Camera(CameraProtocol):
    def __init__(self, index: int, name: str) -> None:

        # camera settings
        cam_raw = {"size": (2304, 1296)}
        cam_main = {"size": (640, 480)}
        cam_controls = {
            "FrameDurationLimits": (33333, 33333),
            "AfMode": controls.AfModeEnum.Manual,
            "LensPosition": 0.0,
        }
        encoder_quality = Quality.VERY_LOW  # VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH

        self.index = index
        self.name = name
        self.encoder_quality = encoder_quality
        self.encoder = H264Encoder()
        self.cam = Picamera2(index)
        self.config = self.cam.create_video_configuration(
            raw=cam_raw, main=cam_main, controls=cam_controls
        )
        self.cam.align_configuration(self.config)
        self.cam.configure(self.config)
        self.path_video = settings.get("DATA_DIRECTORY") + "/videos/" + name + ".mp4"
        self.output = FfmpegOutput(self.path_video)
        self.cam.pre_callback = self.pre_process

        # labels settings
        self.origin_frame_number = (0, 30)
        self.origin_timestamps = (0, 60)
        self.origin_area1 = (0, 90)
        self.origin_area2 = (0, 120)
        self.origin_area3 = (0, 150)
        self.origin_area4 = (0, 180)

        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.scale = 0.5
        self.thickness_line = 2
        self.thickness_text = 1

        # area and threshold settings
        self.area1 = settings.get("AREA1_" + name)
        self.area2 = settings.get("AREA2_" + name)
        self.area3 = settings.get("AREA3_" + name)
        self.area4 = settings.get("AREA4_" + name)

        # detection settings
        self.no_mouse = settings.get("NO_MOUSE_" + name)
        self.one_mouse = settings.get("ONE_MOUSE_" + name)
        self.two_mice = settings.get("TWO_MICE_" + name)

        self.frame_number = 0
        self.timestamp = ""

        self.cam.start()

    def start_camera(self) -> None:
        self.cam.start()

    def stop_preview(self) -> None:
        self.cam.stop_preview()

    def stop_window_preview(self) -> None:
        self.window.cleanup()
        self.cam.start_preview(Preview.NULL)

    def start_record(self) -> None:
        self.cam.start_encoder(self.encoder, self.output, quality=self.encoder_quality)

    def stop_record(self) -> None:
        self.cam.stop_encoder()

    def stop(self) -> None:
        self.cam.stop()

    def change_focus(self, lensposition: float) -> None:
        assert (
            lensposition <= 10 and lensposition >= 0
        ), "lensposition must be a value between 0 and 10"
        self.cam.set_controls({"LensPosition": lensposition})

    def change_framerate(self, framerate: int):
        limit = int(1000000.0 / float(framerate))
        # limit is both min and max number of microseconds for each frame
        self.cam.set_controls({"FrameDurationLimits": (limit, limit)})

    def print_info_about_config(self) -> None:
        print("INFO ABOUT THE " + self.name + " CAM CONFIGURATION:")
        pprint(self.config)
        print()

    def pre_process(self, request: Any) -> None:
        self.frame_number += 1
        self.timestamp = time.strftime("%Y-%m-%d %X")
        with MappedArray(request, "main") as m:
            self.write_frame_number_and_timestamp(m)

            cv2.rectangle(
                m.array,
                (self.area1[0], self.area1[1]),
                (self.area1[2], self.area1[3]),
                app.color_area1,
                self.thickness_line,
            )

            cv2.rectangle(
                m.array,
                (self.area2[0], self.area2[1]),
                (self.area2[2], self.area2[3]),
                app.color_area2,
                self.thickness_line,
            )

            cv2.rectangle(
                m.array,
                (self.area3[0], self.area3[1]),
                (self.area3[2], self.area3[3]),
                app.color_area3,
                self.thickness_line,
            )

    def write_frame_number_and_timestamp(self, m: MappedArray) -> None:
        cv2.putText(
            m.array,
            str(self.frame_number),
            self.origin_frame_number,
            self.font,
            self.scale,
            app.color_frame_number,
            self.thickness_text,
        )

        cv2.putText(
            m.array,
            self.timestamp,
            self.origin_timestamps,
            self.font,
            self.scale,
            app.color_timestamp,
            self.thickness_text,
        )

    def start_preview_window(self) -> QWidget:
        self.stop_preview()
        self.window = QGlPicamera2(self.cam)
        return self.window


# TODO: this function creates a new camera?
# it does not return a pointer to an existing one?
def get_camera(index, name) -> CameraProtocol:
    try:
        cam = Camera(index, name)
        log("Successfully imported cam ", name)
        return cam
    except Exception:
        log("Could not create cam ", name)
        return NullCamera()


cam_corridor = get_camera(0, "CORRIDOR")
cam_box = get_camera(1, "BOX")
cam_corridor.start_record()
cam_box.start_record()
