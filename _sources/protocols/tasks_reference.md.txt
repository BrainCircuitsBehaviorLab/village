## Task Reference

Everything a task can use: the methods you write, the methods you can call, the
attributes of the task and the Bpod primitives. Most of it is the same with Bpod,
with an Arduino or with the Raspberry Pi alone; what only works with one of them is
marked. For how to write a task, see [Tasks (Bpod)](tasks_bpod.md),
[Tasks (Arduino)](tasks_arduino.md) and [Tasks (Raspberry Only)](tasks_raspberry.md).

---

### The methods you write

| Method | Called | Use it to |
| :--- | :--- | :--- |
| `__init__(self)` | When the task is loaded. | Call `super().__init__()` and set `self.info`, the description shown in the GUI. |
| `start(self)` | Once, before the first trial. | Compute what the whole session needs: valve times, sounds, stimulus positions... Without Bpod, also open the connections the task needs (the serial port of the Arduino...). |
| `create_trial(self)` | At the start of every trial. | **With Bpod:** build the state machine of the trial with `self.bpod.add_state`; Bpod runs it when `create_trial` returns. **Without Bpod:** run the trial: call `register_start_trial`, and register everything that happens until the trial is over. |
| `after_trial(self)` | After every trial. | Read `self.trial_data`, decide the outcome, and save values with `register_value`. Registering `water` is mandatory. |
| `close(self)` | Once, after the last trial (session finished, stopped, or error). | Close files or connections. Usually `pass`. |

```{admonition} Register water in every trial
:class: warning
Call `self.register_value("water", ...)` in every `after_trial`, with the microliters
delivered in the trial (`0` if none). The system adds them up to know how much each
subject drinks, and raises an alarm if it is too little.
```

---

### Methods you can call

#### All controllers

| Method | Use |
| :--- | :--- |
| `self.register_value(name, value)` | Saves a value in the trial's row of the session file (a column named `name`). Call it in `after_trial`. |
| `self.register_raspberry_event(name, timestamp)` | Records an event that happened on the Raspberry Pi (a camera detection, a touch...) with `time_utils.now_timestamp()` as timestamp. If it happens during a trial, it is added to `trial_data`. |
| `self.execute_function(i)` | Runs direct function `i` (1-98), see [Direct Functions](functions.md). |

`time_utils` is imported with `from village.scripts.time_utils import time_utils`.

#### Without Bpod

With an Arduino, or with the Raspberry Pi alone (`BEHAVIOR_CONTROLLER` set to
`OTHER`), the task records the trial itself:

| Method | Use |
| :--- | :--- |
| `self.register_start_trial(raspberry_timestamp, controller_timestamp)` | **Required** at the start of every trial, in `create_trial`: without it the task stops with an error. Pass `time_utils.now_timestamp()` and the controller's time at the same moment (with the Raspberry Pi alone, `time_utils.now_timestamp()` as both). |
| `self.register_end_trial(controller_timestamp)` | Ends the trial. Optional: if `create_trial` returns without calling it, the trial is ended at that moment. |
| `self.register_enter_state(state_name, controller_timestamp)` | Enters a state: closes the previous one and opens this one, as Bpod does. |
| `self.register_controller_event(name, controller_timestamp)` | An event detected and timed by the controller (e.g. `"Port1In"` from the Arduino). With the Raspberry Pi alone it does the same as `register_raspberry_event`. |

These methods, and `register_raspberry_event`, only record what happens between
`register_start_trial` and the end of the trial: anything registered outside that
window is ignored.

#### With Bpod

| Method | Use |
| :--- | :--- |
| `self.bpod.add_state(state_name, state_timer, state_change_conditions, output_actions)` | Adds a state to the trial's state machine, see [Bpod primitives](bpod-primitives). |
| `self.bpod.set_global_timer(timer_id, timer_duration)` | Configures a global timer, see [Global timers](#global-timers-counters-and-conditions). |
| `self.bpod.set_global_counter(counter_number, target_event, threshold)` | Configures a global counter. |
| `self.bpod.set_condition(condition_number, condition_channel, channel_value)` | Configures a condition. |
| `self.bpod.send_softcode_to_bpod(i)` | Sends softcode `i` from the Raspberry Pi to Bpod, see [Softcodes](softcodes). |

---

### Attributes

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `self.settings` | `Settings` | The subject's training settings, defined in the [training protocol](creating.md) (e.g. `self.settings.reward_volume`). Changes made during the session are kept for the next one. |
| `self.calibrations` | `Calibrations` | Calibrations, e.g. `self.calibrations.water_calibration.get_valve_time(port, volume)` or `self.calibrations.sound_calibration.get_sound_gain(speaker, dB, sound_name)`. |
| `self.trial_data` | `dict` | Everything that happened in the trial, available in `after_trial` (see [Trial data](tasks_bpod.md#trial-data)). |
| `self.bpod` | `BpodController` | The Bpod interface (see the methods above). Only with Bpod. |
| `self.info` | `str` | Description of the task, shown when it is selected in the GUI. Set it in `__init__`. |
| `self.name` | `str` | The name of the task, which is the name of its class (e.g. `"Bpod1Habituation"`). |
| `self.subject` | `str` | The name of the subject (`"None"` when a task is launched manually without a subject). |
| `self.current_trial` | `int` | The number of the current trial, starting from 1. |
| `self.system_name` | `str` | The name of the system (`SYSTEM_NAME` in `SETTINGS`). |
| `self.date` | `str` | The date and time the session started (`"2026-11-07 10:30:00"`). |
| `self.run_mode` | `str` | `"Auto"` or `"Manual"`. |
| `self.chrono` | `Chrono` | `self.chrono.get_time()` is the time in seconds since the session started. |
| `self.force_stop` | `bool` | Set it to `True` to end the session (see [Ending the session from the task](force-stop)). |
| `self.stop_button_pressed` | `bool` | `True` once the STOP button has been pressed. Read it, don't set it. |
| `self.should_stop` | `bool` | `True` once any stopping condition is met (read-only). Without Bpod, check it in every waiting loop of `create_trial`. |
| `self.system_state` | `State` | The state of the system, e.g. `State.RUN_OPEN` (Auto mode, the subject can leave the box). Import `State` from `village.classes.enums`. |
| `self.cam_box` | `Camera` | The box camera (see [Camera](../devices/camera.md)). |
| `self.gpio` | `Gpio` | The GPIO output pin: `set_on()` / `set_off()` (see [GPIO](../devices/gpio.md)). |
| `self.custom_areas` | `dict` | The detection areas with a custom shape, if the project defines any (see [Camera](../devices/camera.md#custom-detection-area)). |

You can also add your own attributes (`self.side = "left"`): they are kept from one
method to the next, and the triggers and direct functions can read them through
`self.task`.

---

(bpod-primitives)=
### Bpod primitives

`BpodEvent` and `BpodOutput` are imported together with `TaskBase`:

```python
from village.custom_classes.task_base import BpodEvent, BpodOutput, TaskBase
```

A state is added with:

```python
self.bpod.add_state(
    state_name="light_on",           # any name; "exit" ends the trial
    state_timer=5,                   # seconds until the Tup event (0: no timer)
    state_change_conditions={        # event -> next state
        BpodEvent.Port2In: "reward",
        BpodEvent.Tup: "exit",
    },
    output_actions=[(BpodOutput.PWM2, 255)],  # what is on during the state
)
```

The trial starts in the first state added and ends when a transition goes to
`"exit"`. Every state turns off all the outputs of the previous one and turns on only
its own `output_actions`, so there is no need to turn anything off. A state with
`state_timer=0` and no `Tup` condition waits for its events indefinitely; with
`state_timer=0` and a `Tup` condition, it fires its outputs and moves on at once.

#### Events

Used as keys of `state_change_conditions`:

| Event | When it happens |
| :--- | :--- |
| `BpodEvent.Tup` | The state's timer (`state_timer`) runs out. |
| `BpodEvent.Port1In` ... `Port8In` | The animal pokes into port N (its infrared beam is broken). |
| `BpodEvent.Port1Out` ... `Port8Out` | The animal leaves port N. |
| `BpodEvent.BNC1High`, `BNC1Low`, `BNC2High`, `BNC2Low` | A TTL signal on a BNC input goes high or low. |
| `BpodEvent.SoftCode1`, `SoftCode2`... | The Raspberry Pi sent that softcode with `self.bpod.send_softcode_to_bpod(i)`. |
| `BpodEvent.GlobalTimer1Start` ... `GlobalTimer5Start`, `GlobalTimer1End` ... `GlobalTimer5End` | A global timer starts or ends. |
| `BpodEvent.GlobalCounter1End` ... `GlobalCounter5End` | A global counter reaches its threshold. |
| `BpodEvent.Condition1` ... `Condition16` | A condition is true. |

#### Outputs

Used in `output_actions`:

| Output | What it does |
| :--- | :--- |
| `(BpodOutput.PWM1, value)` ... `PWM8` | Turns on the LED of port N with an intensity from 0 to 255. |
| `BpodOutput.Valve1` ... `Valve8` | Opens the valve of port N during the state: use the valve time as `state_timer`. |
| `BpodOutput.BNC1High`, `BNC2High` | Sets a BNC output high (a TTL to another device) during the state. |
| `BpodOutput.SoftCode1` ... `SoftCode98` | Makes the Raspberry Pi run direct function N, at the moment the state starts. |
| `BpodOutput.GlobalTimer1Trig` ... `GlobalTimer5Trig` | Starts a global timer. |
| `BpodOutput.GlobalTimer1Cancel` ... `GlobalTimer5Cancel` | Cancels a global timer. |
| `BpodOutput.GlobalCounter1Reset` ... `GlobalCounter5Reset` | Resets a global counter to 0. |

[bpod_outputs_and_events.py](../examples/bpod_outputs_and_events.md) shows the
ports, LEDs, valves and softcodes in a single task.

(softcodes)=
#### Softcodes

While Bpod runs a trial, the task's Python code is waiting. Softcodes connect the
Raspberry Pi and Bpod during the trial, in both directions:

- **Bpod → Raspberry Pi**: `BpodOutput.SoftCodeN` in the `output_actions` of a state
  runs direct function N on the Raspberry Pi when the state starts: to play a sound,
  show an image... See [Playing a sound](tasks_bpod.md#playing-a-sound) and
  [Direct Functions](functions.md).
- **Raspberry Pi → Bpod**: `self.bpod.send_softcode_to_bpod(N)` produces the event
  `BpodEvent.SoftCodeN` in the state machine, so the trial can react to something
  only the Raspberry Pi sees. It is usually sent from a trigger (which reaches the task
  as `self.task`). For example, to give water when the animal enters box area 1, in
  `camera_trigger.py`:

  ```python
  class CameraTrigger(CameraTriggerBase):
      def __init__(self) -> None:
          super().__init__()
          self.inside = False

      def trigger(self, cam: Camera) -> None:
          if cam.name != "BOX":
              return
          # only when the animal enters, not on every frame while it is inside
          if cam.area1_is_triggered and not self.inside:
              self.task.bpod.send_softcode_to_bpod(1)
          self.inside = cam.area1_is_triggered
  ```

  and in the task, a state that waits for it:

  ```python
  self.bpod.add_state(
      state_name="wait_area1",
      state_timer=60,
      state_change_conditions={
          BpodEvent.SoftCode1: "reward",  # sent by camera_trigger.py
          BpodEvent.Tup: "exit",
      },
      output_actions=[],
  )
  ```

  See [bpod_area2_sound.py](../examples/bpod_area2_sound.md) for the camera, and
  [bpod_touchscreen.py](../examples/bpod_touchscreen.md) for the touchscreen.

#### Global timers, counters and conditions

They are configured in `create_trial`, before or after adding the states, and are
used by all the states of the trial:

- **Global timers** (1 to 5): a timer that keeps running across states, independently
  of each state's own timer, e.g. a deadline for the whole trial. Configure it with
  `self.bpod.set_global_timer(timer_id=1, timer_duration=10)`, start it with the
  output `BpodOutput.GlobalTimer1Trig` and react to `BpodEvent.GlobalTimer1End`. See
  [bpod_global_timer.py](../examples/bpod_global_timer.md).
- **Global counters** (1 to 5): count an event across states. Configure it with
  `self.bpod.set_global_counter(counter_number=1, target_event=BpodEvent.Port2In,
  threshold=5)` and react to `BpodEvent.GlobalCounter1End`, which happens when the
  event has happened 5 times.
- **Conditions** (1 to 16): check the current level of an input at the moment of a
  transition, instead of reacting to a change. Configure it with
  `self.bpod.set_condition(condition_number=1, condition_channel="Port2",
  channel_value=1)` (true while the animal is in port 2) and use
  `BpodEvent.Condition1` in `state_change_conditions`.

For more details and for Bpod modules, see the
[Bpod documentation](https://sanworks.github.io/Bpod_Wiki/).

---

(force-stop)=
### Ending the session from the task

Set `self.force_stop = True` to end the session. The session ends at once, so set it
in `after_trial`, when the trial is already complete: set during a trial (from a
trigger or a direct function), it cuts that trial. It works in Auto mode too: the
session is saved and the subject is let out, as when `maximum_duration` is reached,
even before `minimum_duration`. For example, to stop after a maximum number of trials
(`max_trials` defined in the training protocol):

```python
def after_trial(self):
    ...
    if self.current_trial >= self.settings.max_trials:
        self.force_stop = True
```

The same works for any criterion: an amount of water, a number of correct trials...
