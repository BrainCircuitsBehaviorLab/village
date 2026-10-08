from PyQt5.QtGui import QColor
from sound_functions import tone_generator, whitenoise_generator
from video_functions import (
    draw_circle_generator,
    draw_image_generator,
    draw_image_with_alpha_generator,
    draw_moving_circle_generator,
    draw_rectangle_generator,
    draw_rectangles_generator,
    draw_triangle_generator,
    draw_video_generator,
)

from village.custom_classes.direct_functions_base import DirectFunctionsBase
from village.devices.camera import cam_box
from village.devices.screen import screen
from village.devices.sound_device import sound_device
from village.scripts.time_utils import time_utils


class DirectFunctions(DirectFunctionsBase):

    def function1(self):
        """Play Fixed Sound"""
        # plays a short (1s) white noise burst at a fixed, uncalibrated gain
        # (0.05), the same on both speakers. Useful as a quick test beep.
        gain = 0.05
        duration = 1
        sound = whitenoise_generator(duration=duration, gain=gain)
        sound_device.load(left=sound, right=sound)
        sound_device.play()

    def function2(self):
        """Load Noise Sound"""
        # loads (does not play) a 600Hz tone at a calibrated 70dB, only on the
        # left speaker (the right one stays silent). Needs the "tone_600" sound
        # to be calibrated for speaker 0 in the Sound Calibration panel, or it
        # raises an error. Call function4 afterward to actually play it.
        gain = self.task.calibrations.sound_calibration.get_sound_gain(
            speaker=0, dB=70, sound_name="tone_600"
        )
        duration = 2.5
        sound = tone_generator(duration=duration, gain=gain, frequency=600)
        sound_device.load(left=sound, right=None)

    def function3(self):
        """Load wav sound"""
        # loads a .wav file, applying each speaker's calibrated gain to reach
        # 70dB (using the generic "whitenoise" calibration). self.task.sound_file
        # must be the filename of a .wav file inside the project's "media"
        # folder (MEDIA_DIRECTORY), set by the running task. Needs a "whitenoise"
        # calibration saved for both speakers (0 and 1).
        gain_left = self.task.calibrations.sound_calibration.get_sound_gain(
            speaker=0, dB=70, sound_name="whitenoise"
        )
        gain_right = self.task.calibrations.sound_calibration.get_sound_gain(
            speaker=1, dB=70, sound_name="whitenoise"
        )
        sound_file = self.task.sound_file
        sound_left, sound_right = sound_device.get_sound_from_wav(
            file=sound_file, gain=1.0
        )
        sound_left *= gain_left
        sound_right *= gain_right
        sound_device.load(left=sound_left, right=sound_right)

    def function4(self):
        """Play Loaded Sound"""
        # plays whatever sound was loaded previously (e.g. by function1,
        # function2, or function3).
        sound_device.play()

    def function5(self):
        """Stop Sound"""
        # stops any sound currently playing.
        sound_device.stop()

    def function6(self):
        """Camera MSG ON"""
        # turns on the "ON" text overlay on the BOX camera recording, useful to
        # visually mark a period on the video. Cleared with function7.
        cam_box.annotation = "ON"

    def function7(self):
        """Clear Camera MSG"""
        # clears the text overlay set by function6.
        cam_box.annotation = ""

    def function8(self):
        """White Circle"""
        # draws a white circle at the position defined by the running task
        # (stimulus_x_pos, stimulus_y_pos) for stimulus_duration seconds. These
        # 3 values must be set on the running task (self.task).
        duration = self.task.stimulus_duration
        x_pos = self.task.stimulus_x_pos
        y_pos = self.task.stimulus_y_pos
        diameter = 300
        color = QColor("white")
        draw_function = draw_circle_generator(
            duration=duration, x_pos=x_pos, y_pos=y_pos, diameter=diameter, color=color
        )
        screen.load_draw_function(draw_fn=draw_function)

    def function9(self):
        """Red Rectangle"""
        # draws a red rectangle at the position defined by the running task, for
        # stimulus_duration seconds (set on the running task).
        duration = self.task.stimulus_duration
        x_pos = self.task.stimulus_x_pos
        y_pos = self.task.stimulus_y_pos
        width = 300
        height = 300
        color = QColor("#FF0000")
        draw_function = draw_rectangle_generator(
            duration=duration,
            x_pos=x_pos,
            y_pos=y_pos,
            width=width,
            height=height,
            color=color,
        )
        screen.load_draw_function(draw_fn=draw_function)

    def function10(self):
        """Moving Circle"""
        # draws a white circle that oscillates horizontally at the center of the
        # screen, for stimulus_duration seconds (set on the running task).
        duration = self.task.stimulus_duration
        diameter = 300
        color = QColor("white")
        draw_function = draw_moving_circle_generator(
            duration=duration, diameter=diameter, color=color
        )
        screen.load_draw_function(draw_fn=draw_function)

    def function11(self):
        """Green Triangle"""
        # draws a green triangle indefinitely, until another action interrupts
        # it (we use a very high duration as a trick).
        duration = 100000
        color = QColor("green")
        draw_function = draw_triangle_generator(duration=duration, color=color)
        screen.load_draw_function(draw_fn=draw_function)

    def function12(self):
        """Show Image"""
        # draws the image self.task.image_file at the position defined by the
        # running task, for stimulus_duration seconds. image_file must be the
        # filename of an image inside the project's "media" folder
        # (MEDIA_DIRECTORY).
        duration = self.task.stimulus_duration
        x_pos = self.task.stimulus_x_pos
        y_pos = self.task.stimulus_y_pos
        image_file = self.task.image_file

        draw_function = draw_image_generator(
            duration=duration, x_pos=x_pos, y_pos=y_pos
        )
        screen.load_draw_function(draw_fn=draw_function)
        screen.load_image(file=image_file)

    def function13(self):
        """Image Alpha"""
        # same as function12 but with an alpha channel (for PNG images with
        # transparency), using self.task.image_file2 instead of image_file.
        duration = self.task.stimulus_duration
        x_pos = self.task.stimulus_x_pos
        y_pos = self.task.stimulus_y_pos
        image_file = self.task.image_file2

        draw_function = draw_image_with_alpha_generator(
            duration=duration, x_pos=x_pos, y_pos=y_pos
        )
        screen.load_draw_function(draw_fn=draw_function)
        screen.load_image(file=image_file)

    def function14(self):
        """Play Video"""
        # plays the video self.task.video_file for stimulus_duration seconds,
        # with its audio volume scaled by self.task.volume_gain (0-1). video_file
        # must be the filename of a video inside the project's "media" folder
        # (MEDIA_DIRECTORY).
        duration = self.task.stimulus_duration
        video_file = self.task.video_file
        volume_gain = self.task.volume_gain

        draw_function = draw_video_generator(duration=duration)
        screen.load_draw_function(draw_fn=draw_function)
        screen.load_video(file=video_file, volume_gain=volume_gain)

    def function15(self):
        """Start Drawing"""
        # starts drawing on the screen whatever was loaded with
        # load_draw_function (e.g. by function8-14). Without this, nothing that
        # was loaded is shown.
        screen.start_drawing()

    def function16(self):
        """Stop Drawing"""
        # stops drawing on the screen.
        screen.stop_drawing()

    def function17(self):
        """Set Background"""
        # changes the screen's background color (used to clear it in every draw
        # function). The change is persistent until changed again.
        screen.background_color = QColor(100, 100, 100)

    def function18(self):
        """Show Touchscreen Menu"""
        # draws self.task.rects (a list of (x_pos, y_pos, width, height)
        # tuples, one per clickable zone) as same-colored rectangles that
        # stay up indefinitely -- touch_trigger.py maps a touch inside one
        # of them to a direct function of its own (see raspberry_touchscreen.py).
        rects = self.task.rects
        duration = 100000  # indefinite, same trick as function11
        color = QColor("white")
        draw_function = draw_rectangles_generator(
            rects=rects,
            colors=[color] * len(rects),
            durations=[duration] * len(rects),
        )
        screen.load_draw_function(draw_fn=draw_function)
        screen.start_drawing()

    def function19(self):
        """Show Long/Short Rectangles"""
        # draws self.task.long_rect for self.task.long_duration seconds and
        # self.task.short_rect for the shorter self.task.short_duration --
        # the short one disappears first, while the long one (and the
        # response window) is still running. See bpod_touchscreen.py.
        draw_function = draw_rectangles_generator(
            rects=[self.task.long_rect, self.task.short_rect],
            colors=[QColor("green"), QColor("red")],
            durations=[self.task.long_duration, self.task.short_duration],
        )
        screen.load_draw_function(draw_fn=draw_function)
        screen.start_drawing()

    def function50(self):
        """Click + Sound"""
        # Gated on the OptoGrid's battery level. self.task.og is the OptoGrid
        # instance created (and connected/logging) in the running task's
        # start() -- see raspberry_optogrid_demo.py.
        og = self.task.og
        battery_mv = og.read_battery_mv()

        # Battery range is roughly 3500 (empty) to 4200 mV (full) -- keep
        # going only above 3900 mV.
        if battery_mv is not None and battery_mv > 3900:
            # 1. Register the click as a Raspberry-side event.
            self.task.register_raspberry_event(
                "button_click", time_utils.now_timestamp()
            )
            # 2. Mark this moment in the OptoGrid's own IMU data stream.
            og.sync(self.task.current_trial)
            # 3. Play the sound loaded in the task's start().
            sound_device.play()
            # Let create_trial's waiting loop know the sound was played.
            self.task.sound_played_event.set()
        else:
            print("not enough battery")
