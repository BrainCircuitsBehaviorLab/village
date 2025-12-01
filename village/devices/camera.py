import os
import time
import traceback
from pprint import pprint
from typing import Any

import cv2
import numpy as np
import pandas as pd

from village.classes.enums import Active, AreaActive

try:
    from libcamera import controls
    from picamera2 import MappedArray, Picamera2, Preview
    from picamera2.encoders import H264Encoder, Quality
    from picamera2.outputs import FfmpegOutput
    from picamera2.previews.qt import QPicamera2
except Exception:
    pass

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget

from village.classes.abstract_classes import CameraBase
from village.manager import manager
from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.settings import Color, settings

# info about picamera2: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf

# to debug errors
# Picamera2.set_logging(Picamera2.DEBUG)
# logging.basicConfig(
#     filename="camera_errors.log",
#     filemode="a",
#     format="%(asctime)s %(levelname)s %(name)s: %(message)s",
#     level=logging.DEBUG
# )


# use this function to get info
def print_info_about_the_connected_cameras() -> None:
    print("INFO ABOUT THE CONNECTED CAMERAS:")
    pprint(Picamera2.global_camera_info())
    print()


# the preview class
class LowFreqQPicamera2(QPicamera2):
    def __init__(self, picam2, *args, framerate, **kwargs) -> None:
        super().__init__(picam2, *args, **kwargs)
        self._frame_counter = 0
        self._good_frame = framerate // int(settings.get("CAM_PREVIEWS_FRAMERATE"))

    def render_request(self, completed_request) -> None:
        self._frame_counter += 1
        if self._frame_counter == self._good_frame:
            self._frame_counter = 0
            super().render_request(completed_request)


# the camera class
class Camera(CameraBase):
    def __init__(self, index: int, framerate: int, name: str) -> None:

        frame_duration = int(1000000 / framerate)

        if name == "BOX":
            resolution = settings.get("CAM_BOX_RESOLUTION")
        else:
            resolution = [640, 480]

        self.width = resolution[0]
        self.height = resolution[1]

        # camera settings
        cam_raw = {"size": (2304, 1296)}
        cam_main = {"size": (self.width, self.height)}
        cam_controls = {
            "NoiseReductionMode": controls.draft.NoiseReductionModeEnum.Fast,
            "FrameDurationLimits": (frame_duration, frame_duration),
            "AfMode": controls.AfModeEnum.Manual,
            "LensPosition": 1.0,
            "Sharpness": 1.0,
            "Contrast": 1.0,
        }
        encoder_quality = Quality.VERY_LOW  # VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH

        self.index = index
        self.name = name
        self.framerate = framerate
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
        self.path_picture = os.path.join(
            settings.get("SYSTEM_DIRECTORY"), name + ".jpg"
        )
        self.output = FfmpegOutput(self.path_video)
        self.filename = ""
        self.cam.pre_callback = self.pre_process

        color_area1 = tuple(settings.get("COLOR_AREA1"))
        color_area2 = tuple(settings.get("COLOR_AREA2"))
        color_area3 = tuple(settings.get("COLOR_AREA3"))
        color_area4 = tuple(settings.get("COLOR_AREA4"))
        self.color_areas = [color_area1, color_area2, color_area3, color_area4]
        self.thickness_line = settings.get("RECTANGLES_LINEWIDTH")
        self.detection_color = tuple(settings.get("COLOR_DETECTION"))
        self.detection_size = settings.get("DETECTION_CIRCLE_SIZE")
        self.color_rectangle = (255, 255, 255)
        self.color_text = (0, 0, 0)
        self.change = True
        self.annotation = ""
        self.trial = 0
        self.tracking = False
        self.x_position = -1
        self.y_position = -1
        self.frames: list[int] = []
        self.timings: list[int] = []
        self.trials: list[int] = []
        self.annotations: list[str] = []
        self.x_positions: list[int] = []
        self.y_positions: list[int] = []
        self.camera_timestamps: list[float] = []
        self.pre_process_timestamps: list[float] = []

        if self.change:
            self.set_properties()
            self.change = False

        self.origin_rectangle = (0, 0)
        self.end_rectangle = (self.width, int(self.height / 12))

        self.origin_text1 = (3, int(self.height / 32))
        self.origin_text2 = (3, int(self.height / 15))

        origin_area1 = (int(self.width * 0.375), int(self.height / 15))
        origin_area2 = (int(self.width * 0.53125), int(self.height / 15))
        origin_area3 = (int(self.width * 0.6875), int(self.height / 15))
        origin_area4 = (int(self.width * 0.84375), int(self.height / 15))

        self.origin_areas = [
            origin_area1,
            origin_area2,
            origin_area3,
            origin_area4,
        ]

        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.scale = self.width * 0.000625
        if self.width <= 640:
            self.thickness_text = 1
        else:
            self.thickness_text = 2

        self.frame_number = 0
        self.chrono = time_utils.Chrono()

        self.masks: list[Any] = [-1, -1, -1, -1]
        self.counts: list[int] = [-1, -1, -1, -1]

        self.error = ""
        self.error_frame = 0

        self.is_recording = False
        self.show_time_info = False

        self.two_mice_detections = 0
        self.prohibited_detections = 0

        self.area4_alarm_timer = time_utils.Timer(3600)
        self.box_alarm_timer = time_utils.Timer(3600)

        self.pre_process_timestamp = time_utils.now_timestamp()
        self.camera_timestamp = self.pre_process_timestamp
        self.watchdog_timer = QTimer()
        self.watchdog_timer.setInterval(20000)
        self.watchdog_timer.timeout.connect(self.watchdog_tick)

        self.cam.start()
        self.watchdog_timer.start()

    def set_properties(self) -> None:
        # black or white detection setting
        self.color: Color = settings.get("DETECTION_COLOR")

        # areas and thresholds settings
        self.areas: list[list[int]] = []
        self.thresholds: list[int] = []
        self.number_of_areas = 4

        for i in range(1, self.number_of_areas + 1):
            self.areas.append(settings.get("AREA" + str(i) + "_" + self.name)[0:4])
            self.thresholds.append(settings.get("AREA" + str(i) + "_" + self.name)[4])

        # areas active and allowed settings
        self.areas_active: list[bool] = []
        self.areas_allowed: list[bool] = []
        self.areas_trigger: list[bool] = []
        self.area1_is_triggered = False
        self.area2_is_triggered = False
        self.area3_is_triggered = False
        self.area4_is_triggered = False

        if self.name == "CORRIDOR":
            self.areas_active = [True, True, True, True]
            self.areas_allowed = [True, True, True, True]
            self.areas_trigger = [False, False, False, False]
        else:
            for i in range(1, self.number_of_areas + 1):
                val = settings.get("USAGE" + str(i) + "_BOX")
                if val == AreaActive.ALLOWED:
                    self.areas_active.append(True)
                    self.areas_allowed.append(True)
                    self.areas_trigger.append(False)
                elif val == AreaActive.TRIGGER:
                    self.areas_active.append(True)
                    self.areas_allowed.append(True)
                    self.areas_trigger.append(True)
                elif val == AreaActive.NOT_ALLOWED:
                    self.areas_active.append(True)
                    self.areas_allowed.append(False)
                    self.areas_trigger.append(False)
                else:
                    self.areas_active.append(False)
                    self.areas_allowed.append(False)
                    self.areas_trigger.append(False)

        # detection settings
        self.zero_or_one_mouse = settings.get("DETECTION_OF_MOUSE_" + self.name)[0]
        self.one_or_two_mice = settings.get("DETECTION_OF_MOUSE_" + self.name)[1]
        self.view_detection = settings.get("VIEW_DETECTION_" + self.name) == Active.ON
        if self.name == "BOX":
            self.tracking = settings.get("CAM_BOX_TRACKING_POSITION") == Active.ON
        else:
            self.tracking = False

        color_area1 = tuple(settings.get("COLOR_AREA1"))
        color_area2 = tuple(settings.get("COLOR_AREA2"))
        color_area3 = tuple(settings.get("COLOR_AREA3"))
        color_area4 = tuple(settings.get("COLOR_AREA4"))
        self.color_areas = [color_area1, color_area2, color_area3, color_area4]
        self.thickness_line = settings.get("RECTANGLES_LINEWIDTH")
        self.detection_color = tuple(settings.get("COLOR_DETECTION"))
        self.detection_size = settings.get("DETECTION_CIRCLE_SIZE")

        # lens position, sharpness and contrast settings
        if self.name == "CORRIDOR" and manager.day:
            lensposition = settings.get("LENS_POSITION_" + self.name)[0]
            sharpness = settings.get("SHARPNESS_" + self.name)[0]
            contrast = settings.get("CONTRAST_" + self.name)[0]
        elif self.name == "CORRIDOR":
            lensposition = settings.get("LENS_POSITION_" + self.name)[1]
            sharpness = settings.get("SHARPNESS_" + self.name)[1]
            contrast = settings.get("CONTRAST_" + self.name)[1]
        else:
            lensposition = settings.get("LENS_POSITION_" + self.name)
            sharpness = settings.get("SHARPNESS_" + self.name)
            contrast = settings.get("CONTRAST_" + self.name)

        self.cam.set_controls({"LensPosition": lensposition})
        self.cam.set_controls({"Sharpness": sharpness})
        self.cam.set_controls({"Contrast": contrast})

    def start_camera(self) -> None:
        self.cam.start()

    def stop_camera(self) -> None:
        self.cam.stop()

    def stop_preview_window(self) -> None:
        if self.cam._preview is not None:
            self.cam.stop_preview()
        self.window.cleanup()
        self.cam.start_preview(Preview.NULL)

    def start_recording(self, path_video: str = "", path_csv: str = "") -> None:
        self.filename = os.path.splitext(os.path.basename(path_video))[0]
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
        self.show_time_info = True
        self.cam.start_encoder(self.encoder, self.output, quality=self.encoder_quality)

    def stop_recording(self) -> None:
        if self.is_recording:
            self.is_recording = False
            self.cam.stop_encoder()
            self.save_csv()
        self.show_time_info = False
        self.reset_values()

    def reset_values(self) -> None:
        self.annotation = ""
        self.trial = 0
        self.frames = []
        self.timings = []
        self.camera_timestamps = []
        self.pre_process_timestamps = []
        self.x_positions = []
        self.y_positions = []
        self.trials = []
        self.annotations = []
        self.frame_number = 0
        self.error = ""
        self.filename = ""
        self.x_position = -1
        self.y_position = -1
        self.area1_is_triggered = False
        self.area2_is_triggered = False
        self.area3_is_triggered = False
        self.area4_is_triggered = False
        self.chrono.reset()
        self.pre_process_timestamp = time_utils.now_timestamp()
        self.camera_timestamp = self.pre_process_timestamp

    def save_csv(self) -> None:
        if self.path_csv == os.path.join(settings.get("VIDEOS_DIRECTORY"), "BOX.csv"):
            return

        if self.tracking:
            frames = tuple(self.frames)
            timings = tuple(self.timings)
            trials = tuple(self.trials)
            annotations = tuple(self.annotations)
            x_positions = tuple(self.x_positions)
            y_positions = tuple(self.y_positions)
            camera_timestamps = tuple(self.camera_timestamps)
            pre_process_timestamps = tuple(self.pre_process_timestamps)

            rows = list(
                zip(
                    frames,
                    timings,
                    trials,
                    annotations,
                    camera_timestamps,
                    pre_process_timestamps,
                    x_positions,
                    y_positions,
                )
            )

            df = pd.DataFrame(
                rows,
                columns=[
                    "frame",
                    "ms",
                    "trial",
                    "annotation",
                    "timestamp",
                    "pre_process_timestamp",
                    "x_position",
                    "y_position",
                ],
            )

        else:
            frames = tuple(self.frames)
            timings = tuple(self.timings)
            trials = tuple(self.trials)
            annotations = tuple(self.annotations)
            camera_timestamps = tuple(self.camera_timestamps)
            pre_process_timestamps = tuple(self.pre_process_timestamps)

            rows = list(
                zip(
                    frames,
                    timings,
                    trials,
                    annotations,
                    camera_timestamps,
                    pre_process_timestamps,
                )
            )

            df = pd.DataFrame(
                rows,
                columns=[
                    "frame",
                    "ms",
                    "trial",
                    "annotation",
                    "timestamp",
                    "pre_process_timestamp",
                ],
            )

        df.to_csv(self.path_csv, index=False, sep=";")

    def print_info_about_config(self) -> None:
        print("INFO ABOUT THE " + self.name + " CAM CONFIGURATION:")
        pprint(self.config)
        print()

    def watchdog_tick(self) -> None:
        if (
            time_utils.now_timestamp() - self.pre_process_timestamp > 10
        ):  # 10 seconds without a frame
            try:
                self.restart_camera()
            except Exception:
                pass

    def restart_camera(self) -> None:
        self.watchdog_timer.stop()
        log.alarm(
            "Camera "
            + self.name
            + " not responding. No frames received for more than "
            + "10 seconds. Restarting the camera.",
            subject=manager.subject.name,
        )
        self.cam.stop_recording()
        self.cam.stop()
        time.sleep(1)
        self.cam.start()
        self.watchdog_timer.start()
        if self.name == "CORRIDOR":
            self.start_recording()

    def pre_process(self, request: Any) -> None:
        if self.change:
            self.set_properties()
            self.change = False
        self.frame_number += 1
        self.timing = self.chrono.get_milliseconds()
        self.pre_process_timestamp = time_utils.now_timestamp()

        with MappedArray(request, "main") as m:
            self.frame = m.array
            if self.frame is not None:
                metadata = request.get_metadata()
                sensor_timestamp = metadata["SensorTimestamp"]
                self.camera_timestamp = time_utils.monotonic_ns_to_timestamps(
                    sensor_timestamp
                )
                self.get_gray_frame()
                self.detect_and_trigger()
                self.draw_detection()
                self.draw_rectangles()
                self.write_texts()
                self.write_pixel_detection()
                self.write_csv()
                if self.name == "BOX" and self.is_recording:
                    self.areas_box_ok()

    def get_gray_frame(self) -> None:
        self.gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

    # @time_utils.measure_time
    def detect_and_trigger(self) -> None:
        if self.color == Color.BLACK:
            if self.tracking:
                self.detect_black_position_contours()
                if self.x_position != -1:
                    self.trigger()
            else:
                self.detect_black()
        else:
            if self.tracking:
                self.detect_white_position_contours()
                if self.x_position != -1:
                    self.trigger()
            else:
                self.detect_white()

    def trigger(self) -> None:
        if self.areas_trigger[0]:
            x1, y1, x2, y2 = self.areas[0]
            self.area1_is_triggered = (
                x1 <= self.x_position <= x2 and y1 <= self.y_position <= y2
            )
        if self.areas_trigger[1]:
            x1, y1, x2, y2 = self.areas[1]
            self.area2_is_triggered = (
                x1 <= self.x_position <= x2 and y1 <= self.y_position <= y2
            )
        if self.areas_trigger[2]:
            x1, y1, x2, y2 = self.areas[2]
            self.area3_is_triggered = (
                x1 <= self.x_position <= x2 and y1 <= self.y_position <= y2
            )
        if self.areas_trigger[3]:
            x1, y1, x2, y2 = self.areas[3]
            self.area4_is_triggered = (
                x1 <= self.x_position <= x2 and y1 <= self.y_position <= y2
            )

        manager.camera_trigger.trigger(self)

    def detect_black(self) -> None:
        for index, (x1, y1, x2, y2) in enumerate(self.areas):
            if self.areas_active[index]:
                roi = self.gray_frame[y1:y2, x1:x2]
                threshold = self.thresholds[index]
                _, thresh = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY_INV)
                self.masks[index] = thresh
                self.counts[index] = cv2.countNonZero(thresh)
            else:
                self.masks[index] = -1
                self.counts[index] = -1

    def detect_white(self) -> None:
        for index, (x1, y1, x2, y2) in enumerate(self.areas):
            if self.areas_active[index]:
                roi = self.gray_frame[y1:y2, x1:x2]
                threshold = self.thresholds[index]
                _, thresh = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY)
                self.masks[index] = thresh
                self.counts[index] = cv2.countNonZero(thresh)
            else:
                self.masks[index] = -1
                self.counts[index] = -1

    def detect_black_position_components(self) -> None:
        mask = np.zeros_like(self.gray_frame, dtype=np.uint8)

        for index, (x1, y1, x2, y2) in enumerate(self.areas):
            if self.areas_active[index]:
                roi = self.gray_frame[y1:y2, x1:x2]
                threshold = self.thresholds[index]
                _, roi_bin = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY_INV)
                sub = mask[y1:y2, x1:x2]
                np.maximum(sub, roi_bin, out=sub)
                self.masks[index] = roi_bin
                self.counts[index] = cv2.countNonZero(roi_bin)
            else:
                self.masks[index] = -1
                self.counts[index] = -1

        num, _, stats, centroids = cv2.connectedComponentsWithStats(
            mask, connectivity=8
        )
        if num > 1:
            areas = stats[1:, cv2.CC_STAT_AREA]
            valid = np.where(areas >= self.zero_or_one_mouse)[0]

            if valid.size > 0:
                index = 1 + valid[np.argmax(areas[valid])]
                cx, cy = centroids[index]
                self.x_position = int(cx)
                self.y_position = int(cy)
            else:
                self.x_position = -1
                self.y_position = -1
        else:
            self.x_position = -1
            self.y_position = -1

    def detect_white_position_components(self) -> None:
        mask = np.zeros_like(self.gray_frame, dtype=np.uint8)

        for index, (x1, y1, x2, y2) in enumerate(self.areas):
            if self.areas_active[index]:
                roi = self.gray_frame[y1:y2, x1:x2]
                threshold = self.thresholds[index]
                _, roi_bin = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY)
                sub = mask[y1:y2, x1:x2]
                np.maximum(sub, roi_bin, out=sub)
                self.masks[index] = roi_bin
                self.counts[index] = cv2.countNonZero(roi_bin)
            else:
                self.masks[index] = -1
                self.counts[index] = -1

        num, _, stats, centroids = cv2.connectedComponentsWithStats(
            mask, connectivity=8
        )
        if num > 1:
            areas = stats[1:, cv2.CC_STAT_AREA]
            valid = np.where(areas >= self.zero_or_one_mouse)[0]

            if valid.size > 0:
                index = 1 + valid[np.argmax(areas[valid])]
                cx, cy = centroids[index]
                self.x_position = int(cx)
                self.y_position = int(cy)
            else:
                self.x_position = -1
                self.y_position = -1
        else:
            self.x_position = -1
            self.y_position = -1

    def detect_black_position_contours(self) -> None:
        mask = np.zeros_like(self.gray_frame, dtype=np.uint8)
        for index, (x1, y1, x2, y2) in enumerate(self.areas):
            if self.areas_active[index]:
                roi = self.gray_frame[y1:y2, x1:x2]
                threshold = self.thresholds[index]
                _, roi_bin = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY_INV)
                sub = mask[y1:y2, x1:x2]
                np.maximum(sub, roi_bin, out=sub)
                self.masks[index] = roi_bin
                self.counts[index] = cv2.countNonZero(roi_bin)
            else:
                self.masks[index] = -1
                self.counts[index] = -1

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            self.x_position = -1
            self.y_position = -1
            return

        best_c = None
        best_area = 0.0
        for c in contours:
            a = cv2.contourArea(c)
            if a >= self.zero_or_one_mouse and a > best_area:
                best_area = a
                best_c = c

        if best_c is None:
            self.x_position = -1
            self.y_position = -1
            return

        M = cv2.moments(best_c)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            self.x_position = cx
            self.y_position = cy
        else:
            self.x_position = -1
            self.y_position = -1

    def detect_white_position_contours(self) -> None:
        mask = np.zeros_like(self.gray_frame, dtype=np.uint8)
        for index, (x1, y1, x2, y2) in enumerate(self.areas):
            if self.areas_active[index]:
                roi = self.gray_frame[y1:y2, x1:x2]
                threshold = self.thresholds[index]
                _, roi_bin = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY)
                sub = mask[y1:y2, x1:x2]
                np.maximum(sub, roi_bin, out=sub)
                self.masks[index] = roi_bin
                self.counts[index] = cv2.countNonZero(roi_bin)
            else:
                self.masks[index] = -1
                self.counts[index] = -1

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            self.x_position = -1
            self.y_position = -1
            return

        best_c = None
        best_area = 0.0
        for c in contours:
            a = cv2.contourArea(c)
            if a >= self.zero_or_one_mouse and a > best_area:
                best_area = a
                best_c = c

        if best_c is None:
            self.x_position = -1
            self.y_position = -1
            return

        M = cv2.moments(best_c)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            self.x_position = cx
            self.y_position = cy
        else:
            self.x_position = -1
            self.y_position = -1

    def draw_detection(self) -> None:
        if self.view_detection:
            if self.color == Color.BLACK:
                self.draw_thresholded_black()
            else:
                self.draw_thresholded_white()
            if self.tracking:
                self.draw_position()

    def draw_rectangles(self) -> None:
        cv2.rectangle(
            self.frame,
            self.origin_rectangle,
            self.end_rectangle,
            self.color_rectangle,
            -1,
        )

        if self.view_detection:
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

    def write_texts(self) -> None:
        if not self.show_time_info:
            self.frame_number = 0
            self.timing = 0

        text_trial = "trial: " + str(self.trial) if self.trial != 0 else ""
        text_filename = (
            self.filename
            if self.filename != ""
            else time_utils.string_from_timestamp(self.pre_process_timestamp)
        )
        text_frame = "frame: " + str(self.frame_number)
        text_timing = time_utils.format_duration(self.timing)

        text1 = text_filename + "  " + text_trial + "  " + self.annotation
        text2 = text_timing + "  " + text_frame

        cv2.putText(
            self.frame,
            text1,
            self.origin_text1,
            self.font,
            self.scale,
            self.color_text,
            self.thickness_text,
        )

        cv2.putText(
            self.frame,
            text2,
            self.origin_text2,
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

    def draw_position(self) -> None:
        if self.x_position != -1 and self.y_position != -1:
            cv2.circle(
                self.frame,
                (self.x_position, self.y_position),
                self.detection_size,
                self.detection_color,
                -1,
            )

    def write_csv(self) -> None:
        if self.is_recording:
            self.frames.append(self.frame_number)
            self.timings.append(self.timing)
            self.trials.append(self.trial)
            self.annotations.append(self.annotation)
            self.pre_process_timestamps.append(self.pre_process_timestamp)
            self.camera_timestamps.append(self.camera_timestamp)
        if self.tracking:
            self.x_positions.append(self.x_position)
            self.y_positions.append(self.y_position)

    def start_preview_window(self) -> QWidget:
        if self.cam._preview is not None:
            self.cam.stop_preview()
        self.window = LowFreqQPicamera2(picam2=self.cam, framerate=self.framerate)
        return self.window

    def write_text(self, text: str) -> None:
        self.annotation = text

    def areas_corridor_ok(self) -> bool:
        if self.counts[0] > self.zero_or_one_mouse:
            log.info(
                "Detection in area1: " + str(self.counts[0]),
                subject=manager.subject.name,
            )
            return False
        elif self.counts[1] > self.zero_or_one_mouse:
            log.info(
                "Detection in area2: " + str(self.counts[1]),
                subject=manager.subject.name,
            )
            return False
        elif self.counts[2] > self.one_or_two_mice:
            log.info(
                "Large detection in area3: " + str(self.counts[2]),
                subject=manager.subject.name,
            )
            return False
        elif self.counts[3] > self.zero_or_one_mouse:
            text = "Detection in area4 when it should be empty: " + str(self.counts[3])
            if self.area4_alarm_timer.has_elapsed():
                log.alarm(text, subject=manager.subject.name)
            else:
                log.info(text, subject=manager.subject.name)

            return False
        else:
            return True

    def areas_box_ok(self) -> None:
        pixels_allowed = 0
        pixels_not_allowed = 0

        pixels_allowed = sum(
            count for count, allow in zip(self.counts, self.areas_allowed) if allow
        )
        pixels_not_allowed = sum(
            count for count, allow in zip(self.counts, self.areas_allowed) if not allow
        )

        if pixels_allowed > self.one_or_two_mice:
            if self.box_alarm_timer.ten_seconds_elapsed():
                self.two_mice_detections += 1
            if self.two_mice_detections >= 3:
                self.two_mice_detections = 0
                if self.box_alarm_timer.has_elapsed():
                    log.alarm("2 subjects in box. Area: " + str(pixels_allowed))

        elif pixels_not_allowed > self.zero_or_one_mouse:
            if self.box_alarm_timer.ten_seconds_elapsed():
                self.prohibited_detections += 1
            if self.prohibited_detections >= 3:
                self.prohibited_detections = 0
                if self.box_alarm_timer.has_elapsed():
                    log.alarm(
                        "1 subject in prohibited area. Area: " + str(pixels_not_allowed)
                    )

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


def get_camera(index: int, framerate: int, name: str) -> CameraBase:
    try:
        cam = Camera(index, framerate, name)
        log.info("Cam " + name + " successfully initialized")
        return cam
    except Exception:
        log.error("Could not initialize cam " + name, exception=traceback.format_exc())
        return CameraBase()


cam_corridor = get_camera(
    settings.get("CAM_CORRIDOR_INDEX"),
    settings.get("CAM_CORRIDOR_FRAMERATE"),
    "CORRIDOR",
)
cam_box = get_camera(
    settings.get("CAM_BOX_INDEX"), settings.get("CAM_BOX_FRAMERATE"), "BOX"
)
