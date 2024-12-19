import os
import traceback
from pprint import pprint
from typing import Any

import cv2
import pandas as pd

from village.classes.enums import Active, AreaActive

try:
    from libcamera import controls
    from picamera2 import MappedArray, Picamera2, Preview
    from picamera2.encoders import H264Encoder, Quality
    from picamera2.outputs import FfmpegOutput
    from picamera2.previews.qt import QGlPicamera2
except Exception:
    pass

from PyQt5.QtWidgets import QWidget

from village.classes.protocols import CameraProtocol
from village.log import log
from village.manager import manager
from village.settings import Color, settings
from village.time_utils import time_utils

# info about picamera2: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
# configure the logging of libcamera (the C++ library picamera2 uses)
# '0' = DEBUG, '1' = INFO, '2' = WARNING, '3' = ERROR, '4' = FATAL
os.environ["LIBCAMERA_LOG_LEVELS"] = "2"
# Picamera2.set_logging(Picamera2.DEBUG)


# use this function to get info
def print_info_about_the_connected_cameras() -> None:
    print("INFO ABOUT THE CONNECTED CAMERAS:")
    pprint(Picamera2.global_camera_info())
    print()


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
        self.path_video = os.path.join(settings.get("VIDEOS_DIRECTORY"), name + ".mp4")
        self.path_csv = os.path.join(settings.get("VIDEOS_DIRECTORY"), name + ".csv")
        self.path_picture = os.path.join(settings.get("DATA_DIRECTORY"), name + ".jpg")
        # self.output = FfmpegOutput(self.path_video)
        # self.output = FfmpegOutput(
        #     self.path_video, extra_args=["-thread_queue_size", "1024"]
        # )

        # self.output = FfmpegOutput(self.path_video + " -thread_queue_size 1024")
        self.output = FfmpegOutput(self.path_video)
        self.cam.pre_callback = self.pre_process

        color_area1 = settings.get("COLOR_AREA1")
        color_area2 = settings.get("COLOR_AREA2")
        color_area3 = settings.get("COLOR_AREA3")
        color_area4 = settings.get("COLOR_AREA4")
        self.color_areas = [color_area1, color_area2, color_area3, color_area4]
        self.color_rectangle = (255, 255, 255)
        self.color_text = (0, 0, 0)
        self.color_state = (80, 80, 80)
        self.change = True
        self.state = ""
        self.trial = 0
        self.frames: list[int] = []
        self.timings: list[int] = []
        self.trials: list[int] = []
        self.states: list[str] = []

        if self.change:
            self.set_properties()
            self.change = False

        # labels settings
        self.origin_rectangle = (0, 0)
        self.end_rectangle = (640, 40)

        self.origin_timestamps = (20, 15)
        self.origin_trial = (175, 15)
        self.origin_state = (240, 15)

        self.origin_frame_number = (3, 30)
        self.origin_timings = (120, 30)
        origin_area1 = (240, 30)
        origin_area2 = (340, 30)
        origin_area3 = (440, 30)
        origin_area4 = (540, 30)

        self.origin_areas = [
            origin_area1,
            origin_area2,
            origin_area3,
            origin_area4,
        ]

        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.scale = 0.4
        self.thickness_line = 2
        self.thickness_text = 1

        self.frame_number = 0
        self.chrono = time_utils.Chrono()
        self.timestamp = ""

        self.masks: list[Any] = []
        self.counts: list[int] = []
        self.cropped_frames: list[Any] = []

        self.error = ""
        self.error_frame = 0

        self.is_recording = False

        self.area4_alarm_chono = time_utils.Chrono(initial_offset=True)

        self.cam.start()

    def set_properties(self) -> None:
        # black or white detection setting
        self.color: Color = settings.get("DETECTION_COLOR")

        # areas and thresholds settings
        self.areas: list[list[int]] = []
        self.thresholds: list[int] = []
        self.number_of_areas = 4

        threshold_index = 4
        if self.name == "CORRIDOR" and not manager.day:
            threshold_index = 5

        for i in range(1, self.number_of_areas + 1):
            self.areas.append(settings.get("AREA" + str(i) + "_" + self.name)[0:4])
            self.thresholds.append(
                settings.get("AREA" + str(i) + "_" + self.name)[threshold_index]
            )

        # areas active and allowed settings
        self.areas_active: list[bool] = []
        self.areas_allowed: list[bool] = []
        if self.name == "CORRIDOR":
            self.areas_active = [True, True, True, True]
            self.areas_allowed = [True, True, True, True]
        else:
            for i in range(1, self.number_of_areas + 1):
                val = settings.get("USAGE" + str(i) + "_BOX")
                if val == AreaActive.ALLOWED:
                    self.areas_active.append(True)
                    self.areas_allowed.append(True)
                elif val == AreaActive.NOT_ALLOWED:
                    self.areas_active.append(True)
                    self.areas_allowed.append(False)
                else:
                    self.areas_active.append(False)
                    self.areas_allowed.append(False)

        # detection settings
        self.zero_or_one_mouse = settings.get("DETECTION_OF_MOUSE_" + self.name)[0]
        self.one_or_two_mice = settings.get("DETECTION_OF_MOUSE_" + self.name)[1]

        self.no_mouse = settings.get("NO_MOUSE_" + self.name)
        self.one_mouse = settings.get("ONE_MOUSE_" + self.name)
        self.two_mice = settings.get("TWO_MICE_" + self.name)
        self.view_detection = settings.get("VIEW_DETECTION_" + self.name) == Active.ON

    def start_camera(self) -> None:
        self.cam.start()

    def stop_preview_window(self) -> None:
        if self.cam._preview is not None:
            self.cam.stop_preview()
        self.window.cleanup()
        self.cam.start_preview(Preview.NULL)

    def start_record(self, path_video: str = "", path_csv: str = "") -> None:
        time_start = time_utils.now_string_for_filename()
        self.chrono.reset()
        if path_video != "":
            self.path_video = path_video
            self.path_csv = path_csv
        else:
            self.path_video = os.path.join(
                settings.get("VIDEOS_DIRECTORY"),
                self.name + "_" + time_start + ".mp4",
            )
            self.path_csv = os.path.join(
                settings.get("VIDEOS_DIRECTORY"),
                self.name + "_" + time_start + ".csv",
            )
        self.output = FfmpegOutput(self.path_video)
        self.is_recording = True
        self.cam.start_encoder(self.encoder, self.output, quality=self.encoder_quality)

    def stop_record(self) -> None:
        self.cam.stop_encoder()
        self.is_recording = False
        self.save_csv()
        self.reset_values()

    def reset_values(self) -> None:
        self.state = ""
        self.trial = 0
        self.frames = []
        self.timings = []
        self.trials = []
        self.states = []
        self.frame_number = 0
        self.timestamp = ""
        self.error = ""
        self.chrono.reset()

    def save_csv(self) -> None:
        if self.path_csv == os.path.join(settings.get("VIDEOS_DIRECTORY"), "BOX.csv"):
            return

        # if we stop when the last frame is being stored one of this lists
        # may be one unit longer than the others, we remove the last element
        min_length = min(
            len(self.frames), len(self.timings), len(self.trials), len(self.states)
        )

        self.frames = self.frames[:min_length]
        self.timings = self.timings[:min_length]
        self.trials = self.trials[:min_length]
        self.states = self.states[:min_length]

        df = pd.DataFrame(
            {
                "frame": self.frames,
                "ms": self.timings,
                "trial": self.trials,
                "state": self.states,
            }
        )

        df.to_csv(self.path_csv, index=False, sep=";")

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
        if self.change:
            self.set_properties()
            self.change = False
        self.frame_number += 1
        self.timing = self.chrono.get_milliseconds()
        self.timestamp = time_utils.now_string()
        with MappedArray(request, "main") as m:
            self.frame = m.array
            if self.frame is not None:
                self.get_gray_frame()
                self.crop_areas()
                self.detect()
                self.draw_detection()
                self.draw_rectangles()
                self.write_frame_number_and_timestamp()
                self.write_state()
                self.write_trial()
                self.write_pixel_detection()
                self.write_csv()

    def get_gray_frame(self) -> None:
        self.gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

    def crop_areas(self) -> None:
        self.cropped_frames = []
        for f in self.areas:
            self.cropped_frames.append(self.gray_frame[f[1] : f[3], f[0] : f[2]])

    def detect(self) -> None:
        if self.color == Color.BLACK:
            self.detect_black()
        else:
            self.detect_white()

    def detect_black(self) -> None:
        self.masks = []
        self.counts = []
        for index, frame in enumerate(self.cropped_frames):
            if self.areas_active[index]:
                threshold = self.thresholds[index]
                _, thresh = cv2.threshold(frame, threshold, 255, cv2.THRESH_BINARY_INV)
                self.masks.append(thresh)
                self.counts.append(cv2.countNonZero(thresh))
            else:
                self.masks.append(-1)
                self.counts.append(-1)

    def detect_white(self) -> None:
        self.masks = []
        self.counts = []
        for index, frame in enumerate(self.cropped_frames):
            if self.areas_active[index]:
                threshold = self.thresholds[index]
                _, thresh = cv2.threshold(frame, threshold, 255, cv2.THRESH_BINARY)
                self.masks.append(thresh)
                self.counts.append(cv2.countNonZero(thresh))
            else:
                self.masks.append(-1)
                self.counts.append(-1)

    def draw_detection(self) -> None:
        if self.view_detection:
            if self.color == Color.BLACK:
                self.draw_thresholded_black()
            else:
                self.draw_thresholded_white()

    def draw_rectangles(self) -> None:
        cv2.rectangle(
            self.frame,
            self.origin_rectangle,
            self.end_rectangle,
            self.color_rectangle,
            -1,
        )
        for i in range(self.number_of_areas):
            if self.areas_active[i]:
                cv2.rectangle(
                    self.frame,
                    (self.areas[i][0], self.areas[i][1]),
                    (self.areas[i][2], self.areas[i][3]),
                    self.color_areas[i],
                    self.thickness_line,
                )
                if not self.areas_allowed[i]:
                    cv2.line(
                        self.frame,
                        (self.areas[i][0], self.areas[i][1]),
                        (self.areas[i][2], self.areas[i][3]),
                        self.color_areas[i],
                        self.thickness_line,
                    )
                    cv2.line(
                        self.frame,
                        (self.areas[i][2], self.areas[i][1]),
                        (self.areas[i][0], self.areas[i][3]),
                        self.color_areas[i],
                        self.thickness_line,
                    )

    def write_state(self) -> None:
        if self.state == "":
            return

        cv2.putText(
            self.frame,
            self.state,
            self.origin_state,
            self.font,
            self.scale,
            self.color_state,
            self.thickness_text,
        )

    def write_trial(self) -> None:
        if self.trial == 0:
            return

        cv2.putText(
            self.frame,
            "trial: " + str(self.trial),
            self.origin_trial,
            self.font,
            self.scale,
            self.color_text,
            self.thickness_text,
        )

    def write_frame_number_and_timestamp(self) -> None:
        if not self.is_recording:
            self.frame_number = 0
            self.timing = 0

        cv2.putText(
            self.frame,
            self.timestamp,
            self.origin_timestamps,
            self.font,
            self.scale,
            self.color_text,
            self.thickness_text,
        )

        cv2.putText(
            self.frame,
            "frame: " + str(self.frame_number),
            self.origin_frame_number,
            self.font,
            self.scale,
            self.color_text,
            self.thickness_text,
        )

        cv2.putText(
            self.frame,
            "ms: " + str(self.timing),
            self.origin_timings,
            self.font,
            self.scale,
            self.color_text,
            self.thickness_text,
        )

    def write_pixel_detection(self) -> None:
        for i in range(self.number_of_areas):
            if self.areas_active[i]:
                cv2.putText(
                    self.frame,
                    "area" + str(i + 1) + ": " + str(self.counts[i]),
                    self.origin_areas[i],
                    self.font,
                    self.scale,
                    self.color_areas[i],
                    self.thickness_text,
                )

    def draw_thresholded_black(self) -> None:
        for i, f in enumerate(self.areas):
            if self.areas_active[i]:
                try:
                    mask = cv2.bitwise_not(
                        cv2.cvtColor(self.masks[i], cv2.COLOR_GRAY2BGRA)
                    )
                    self.frame[f[1] : f[3], f[0] : f[2]] = cv2.bitwise_and(
                        self.frame[f[1] : f[3], f[0] : f[2]], mask
                    )
                except Exception:
                    pass

    def draw_thresholded_white(self) -> None:
        for i, f in enumerate(self.areas):
            if self.areas_active[i]:
                try:
                    mask = cv2.cvtColor(self.masks[i], cv2.COLOR_GRAY2BGRA)
                    self.frame[f[1] : f[3], f[0] : f[2]] = cv2.bitwise_or(
                        self.frame[f[1] : f[3], f[0] : f[2]], mask
                    )
                except Exception:
                    pass

    def write_csv(self) -> None:
        if self.is_recording:
            self.frames.append(self.frame_number)
            self.timings.append(self.timing)
            self.trials.append(self.trial)
            self.states.append(self.state)

    def start_preview_window(self) -> QWidget:
        if self.cam._preview is not None:
            self.cam.stop_preview()
        self.window = QGlPicamera2(self.cam)
        # self.window.context().setShareContext(shared_context)
        return self.window

    def log(self, text: str) -> None:
        self.state = text

    def areas_corridor_ok(self) -> bool:
        if self.counts[0] > self.zero_or_one_mouse:
            log.info("Detection in area1: " + str(self.counts[0]))
            return False
        elif self.counts[1] > self.zero_or_one_mouse:
            log.info("Detection in area2: " + str(self.counts[1]))
            return False
        elif self.counts[2] > self.one_or_two_mice:
            log.info("Large detection in area3: " + str(self.counts[2]))
            return False
        elif self.counts[3] > self.zero_or_one_mouse:
            text = "Detection in area4: " + str(self.counts[3])
            if self.area4_alarm_chono.get_seconds() > settings.get("ALARM_AREA4_TIME"):
                self.area4_alarm_chono.reset()
                log.alarm(text)
            else:
                log.info(text)

            return False
        else:
            return True

    def area_1_empty(self) -> bool:
        return self.counts[0] <= self.zero_or_one_mouse

    def area_2_empty(self) -> bool:
        return self.counts[1] <= self.zero_or_one_mouse

    def area_3_empty(self) -> bool:
        return self.counts[2] <= self.zero_or_one_mouse

    def area_4_empty(self) -> bool:
        return self.counts[3] <= self.zero_or_one_mouse

    def take_picture(self) -> None:
        self.cam.capture_file(self.path_picture)


def get_camera(index: int, name: str) -> CameraProtocol:
    try:
        cam = Camera(index, name)
        log.info("Cam " + name + " successfully initialized")
        return cam
    except Exception:
        log.error("Could not initialize cam " + name, exception=traceback.format_exc())
        return CameraProtocol()


cam_corridor = get_camera(0, "CORRIDOR")
cam_box = get_camera(1, "BOX")
