import math
import random
import struct

import serial

from village.custom_classes.task_base import TaskBase
from village.scripts.time_utils import time_utils
from village.settings import settings

# Protocol (see arduino_2_passive.ino):
#
# Pi -> Arduino, 6 raw bytes, sent once at the start of each trial:
#   [CMD_START_TRIAL, port,
#    valve_time_ms (uint16, little-endian), led_on_timeout_ms (uint16, LE)]
#   Tells the Arduino which port gets the reward this trial, how long to
#   open its valve for, and how long to then wait for a poke there. From
#   here the Arduino runs the whole trial on its own; the Pi just listens.
#
# Arduino -> Pi, 6 raw bytes per message:
#   [EVENT_POKE, port, elapsed_ms (uint32, LE)]
#     -- once per poke seen on EITHER port during the response window.
#        Only a poke on the correct port ends the window early; a poke on
#        the wrong port is reported too, but the Arduino keeps waiting.
#   [EVENT_STATE, state, elapsed_ms (uint32, LE)]
#     -- every time the Arduino enters a new state (see STATE_NAMES), so it
#        can be registered with register_enter_state, as Bpod does.
#   [EVENT_TRIAL_END, result, elapsed_ms (uint32, LE)]
#     -- once, when the response window is over: RESULT_GOT_CORRECT if the
#        correct port was poked before the timeout (whether or not a wrong
#        poke happened earlier), RESULT_TIMEOUT if it never was.
#   elapsed_ms is milliseconds since the Arduino received CMD_START_TRIAL
#   for THIS trial (its own timer, reset every trial). It is the controller
#   clock: the trial start is registered as controller time 0 at the moment
#   the Pi sent CMD_START_TRIAL, and every elapsed_ms as a controller
#   timestamp (register_controller_event / register_enter_state), so the two
#   clocks never need to be synchronized.
CMD_START_TRIAL = 1

EVENT_POKE = 1
EVENT_TRIAL_END = 2
EVENT_STATE = 3

# State ids sent by the Arduino (same names as bpod_2_passive.py). The ITI
# ("iti") is done by the Pi, after EVENT_TRIAL_END.
STATE_NAMES = {1: "water_delivery", 2: "led_on"}

RESULT_TIMEOUT = 0
RESULT_GOT_CORRECT = 1

BAUDRATE = 9600  # must match the Arduino sketch's Serial.begin(...)
READ_TIMEOUT = 0.05  # seconds; also how often should_stop/deadlines get re-checked
MESSAGE_SIZE = 6  # every Arduino -> Pi message is exactly this many bytes


class Arduino2Passive(TaskBase):

    def __init__(self):
        super().__init__()

        self.info = """
        Passive learning, Water Delivery Task
        ----------------------------------------------------------------
        Habituates the mice to the LEDs and to the ports by delivering the
        reward up front, before any response is required -- purely passive
        learning.
        - Each trial, the Pi picks a port and tells the Arduino everything
          it needs: that port's LED and valve turn on together, the valve
          closes again after its calibrated opening time, and the LED
          stays on afterward for a response window.
        - A poke on the wrong port during that window is recorded but
          doesn't end it -- only a poke on the lit port does, or the
          window running out. Whichever port was poked first,
          chronologically, is what decides the logged outcome; reward has
          already been delivered either way -- the response here is purely
          about the association between the LED and the port, not about
          getting water.
        """

    def start(self):
        """Opens the serial connection to the Arduino, and uses the
        calibration to get the valve opening times (in seconds) for ports 1
        (left) and 3 (right), so they deliver the water volume defined in
        settings.reward_volume.

        Required settings (defined in training_protocol.py):
        - self.settings.reward_volume: reward volume delivered each trial
        - self.settings.led_on_time: max duration of the response window, seconds
        - self.settings.iti_time: inter-trial interval, seconds
        """

        self.serial_port = serial.Serial(
            port=settings.get("CONTROLLER_PORT"),
            baudrate=BAUDRATE,
            timeout=READ_TIMEOUT,
        )
        self.serial_port.reset_input_buffer()

        self.valve_l_time = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_volume
        )
        self.valve_r_time = self.calibrations.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_volume
        )

    def create_trial(self):
        """Picks the trial's port, hands it and the two timings to the
        Arduino in one message, then just listens for whatever it reports
        until it signals the trial is over. The deadline below is only a
        safety net for a lost/garbled message -- in normal operation the
        Arduino's own EVENT_TRIAL_END always arrives well before it.
        """

        self.side = random.choice(["left", "right"])
        if self.side == "left":
            valvetime, port = self.valve_l_time, 1
        else:
            valvetime, port = self.valve_r_time, 3

        valve_time_ms = int(valvetime * 1000)
        led_on_timeout_ms = int(self.settings.led_on_time * 1000)

        self.serial_port.write(
            struct.pack(
                "<BBHH", CMD_START_TRIAL, port, valve_time_ms, led_on_timeout_ms
            )
        )
        t_sent = time_utils.now_timestamp()
        # The Arduino's clock (elapsed_ms) starts at 0 when it gets the command.
        self.register_start_trial(raspberry_timestamp=t_sent, controller_timestamp=0.0)

        self.got_correct_poke = False
        t_end = None  # controller time of EVENT_TRIAL_END
        deadline = (
            t_sent
            + valvetime
            + self.settings.led_on_time
            + self.settings.iti_time
            + 2.0  # margin for serial/USB latency, never expected to matter
        )
        buffer = bytearray()
        while not self.should_stop and time_utils.now_timestamp() < deadline:
            chunk = self.serial_port.read(MESSAGE_SIZE - len(buffer))
            if not chunk:
                continue
            buffer += chunk
            if len(buffer) < MESSAGE_SIZE:
                continue

            event, value, elapsed_ms = struct.unpack("<BBI", bytes(buffer))
            buffer.clear()
            t = elapsed_ms / 1000.0  # controller clock, seconds

            if event == EVENT_STATE:
                self.register_enter_state(STATE_NAMES.get(value, f"state{value}"), t)
            elif event == EVENT_POKE:
                self.register_controller_event(f"Port{value}In", t)
            elif event == EVENT_TRIAL_END:
                self.got_correct_poke = value == RESULT_GOT_CORRECT
                t_end = t
                break

        if t_end is None:
            return  # stopped or lost message: the trial is ended automatically

        if self.got_correct_poke:
            # The ITI is timed by the Pi, starting when the Arduino finished.
            self.register_enter_state("iti", t_end)
            t_end += self.wait(self.settings.iti_time)
        self.register_end_trial(t_end)

    def wait(self, seconds):
        """Waits up to `seconds` (less if the task is asked to stop), discarding
        any stray serial bytes. Returns the time actually waited, in seconds."""

        start = time_utils.now_timestamp()
        while not self.should_stop and time_utils.now_timestamp() < start + seconds:
            self.serial_port.read(MESSAGE_SIZE)
        return time_utils.now_timestamp() - start

    def after_trial(self):
        """Reward was already delivered regardless of the response, so
        water always reflects settings.reward_volume. outcome/response_side
        are worked out from the poke events registered in create_trial: a
        poke on the wrong side doesn't end the response window early, but
        it's still logged, so it still counts as a valid (incorrect)
        response. This is evaluated independently of self.got_correct_poke:
        if a wrong poke happened before an eventual correct one, the
        outcome below is "incorrect" even though the window still ended by
        getting the correct poke.
        """

        t_led_on = self.trial_data.get("STATE_led_on_START", [math.nan])[0]
        left_pokes = [t for t in self.trial_data.get("Port1In", []) if t >= t_led_on]
        right_pokes = [t for t in self.trial_data.get("Port3In", []) if t >= t_led_on]

        if left_pokes and (not right_pokes or left_pokes[0] < right_pokes[0]):
            response_side = "left"
        elif right_pokes:
            response_side = "right"
        else:
            response_side = "none"

        outcome = (
            "miss"
            if response_side == "none"
            else ("correct" if response_side == self.side else "incorrect")
        )

        self.register_value("rewarded_side", self.side)
        self.register_value("water", self.settings.reward_volume)
        self.register_value("outcome", outcome)
        self.register_value("response_side", response_side)

    def close(self):
        """Closes the serial connection to the Arduino."""

        if self.serial_port.is_open:
            self.serial_port.close()
