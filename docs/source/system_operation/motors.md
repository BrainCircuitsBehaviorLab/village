## Motors

The Training Village drives standard hobby servomotors through **PCA9685** PWM
controllers over I2C: one chip on the corridor board (up to 4 door motors) and one
on the box board (up to 7 motors). Each motor is calibrated individually and stored
in its own `MOTORx_VALUES` setting.

### Which motors exist

| Motor | Enabled by | Values setting |
|-------|-----------|----------------|
| Corridor doors 1–2 | always present | `MOTOR1_VALUES`, `MOTOR2_VALUES` |
| Corridor doors 3–4 | `MOTOR3_CORRIDOR`, `MOTOR4_CORRIDOR` | `MOTOR3_VALUES`, `MOTOR4_VALUES` |
| Box motors 1–7 | `MOTOR1_BOX` … `MOTOR7_BOX` | `MOTOR1_BOX_VALUES` … `MOTOR7_BOX_VALUES` |

The corridor motors are enabled under `SETTINGS` → `CORRIDOR SETTINGS` and the box
motors under `SETTINGS` → `BOX SETTINGS`. A motor left `OFF` is replaced by a
`NullMotor`, whose methods accept the same calls and do nothing, so a task that
drives a disabled motor still runs without errors.

---

### Calibration

Motor values are **not** edited from the `SETTINGS` screen. Each motor has its own
`MOTORx VALUES` button in the `MONITOR` screen, under the `CORRIDOR` or `BOX` tab,
which opens a dialog where the values can be changed and tested with `OPEN`/`CLOSE`
before saving. See [Corridor Hardware Setup](corridor.md) for the full calibration
procedure.

Each motor stores five values:

| Field | Meaning |
|-------|---------|
| `open angle` | Angle (0–180°) of the open position |
| `close angle` | Angle (0–180°) of the closed position |
| `open time (ms)` | **Total** milliseconds the travel to open should take. `0` = as fast as the servo can move |
| `close time (ms)` | Same, for the travel to close |
| `hold` | Whether the servo keeps holding torque after arriving (see below) |

Travel time is not a delay: the movement is split into 5° steps and the time is
spread evenly across them, so the door glides instead of snapping. A 30° move with
`close time = 300` performs 6 steps of 50 ms each.

---

### Holding torque

A powered servo actively fights anything that tries to move it. That is usually what
a door wants — but it also means the motor hums continuously and warms up, and for a
mechanism that does not need to resist anything, that is wasted wear and noise.

The `hold` value decides what happens **after** the motor reaches its target:

| `hold` | Behaviour |
|--------|-----------|
| `True` (checked, the default) | The PWM signal keeps running. The servo resists a load and stays exactly in place, but hums and warms up. |
| `False` (unchecked) | The PWM signal is cut once the motor has arrived. The servo goes silent and cool, but anything pushing on it can move it out of position. |

Corridor doors normally want `hold` on, since the door must stay where it was put.
A mechanism that latches mechanically, or that only needs to reach a position and
then be left alone, is better off with it unchecked.

```{admonition} Note
:class: note
When `hold` is off and the travel time is `0` (an instant move), the system waits one
second before cutting the power, so the servo has time to physically get there —
cutting it immediately would leave the motor stranded mid-travel. This wait is the
`MOTOR_SETTLE_MS` constant in `village/devices/chip.py`; a heavier door with a long
travel may need it raised.
```

---

### Using motors in tasks

Import the module-level instance of the motor you need and call it directly:

```python
from village.devices.chip import motor_box1, motor_corridor1

# Move to the calibrated open/close positions, using this motor's saved
# angles, times and hold value
motor_box1.open()
motor_box1.close()

# Override the saved hold value for a single movement
motor_box1.open(hold=False)   # release the servo once it is open
motor_box1.close(hold=True)   # keep this one powered, whatever the setting says

# Move to an arbitrary angle over an arbitrary time
motor_box1.move(120)            # instantly
motor_box1.move(120, 500)       # spread over 500 ms
motor_box1.move(120, 500, hold=False)

# Release holding torque at any later moment
motor_box1.disable()
```

#### Method reference

| Method | Arguments | Description |
|--------|-----------|-------------|
| `open(hold=None, settle_ms=1000)` | — | Moves to the calibrated open angle over the calibrated open time. |
| `close(hold=None, settle_ms=1000)` | — | Moves to the calibrated close angle over the calibrated close time. |
| `move(angle, total_ms=0, hold=None, settle_ms=1000)` | `angle`: 0–180, `total_ms`: total travel time | Moves to an arbitrary angle. |
| `disable()` | — | Cuts the PWM signal, releasing holding torque immediately. |

`hold=None` (the default on all three movement methods) means **use this motor's
saved value**. Pass `hold=True` or `hold=False` to override it for that one call
without changing the setting. `settle_ms` only has an effect when `hold` resolves to
`False`.

---

### These calls never block

Every `open()`, `close()`, `move()` and `disable()` call **returns immediately**. The
movement itself — including the step-by-step ramp, the settle wait and cutting the
power — runs on a background thread, one per PWM chip.

This matters in two ways:

- A task, a GUI button or the corridor state machine can command a 300 ms door
  movement without stalling for 300 ms. Nothing waits for a servo.
- Commands to motors on the **same** chip are executed strictly one at a time, in the
  order they were submitted. Two box motors never move simultaneously, and a
  `close()` issued right after an `open()` always happens after it finishes. The
  corridor chip and the box chip have separate threads, so they do run in parallel
  with each other.

Because the calls return before the movement is done, there is no return value and no
way to wait for completion. If a task needs to know the door has finished, it must
allow for the travel time itself (the `open time`/`close time` it was calibrated
with).

```{admonition} Warning
:class: warning
A motor that was not connected when Village started is not picked up later. After
plugging a motor in, or after enabling one in `SETTINGS`, Village must be restarted —
see [Troubleshooting](../troubleshooting/troubleshooting.md).
```

```{admonition} Note
:class: note
Systems using the legacy corridor board (`OLD_VERSION` enabled in
`SETTINGS` → `ADVANCED SETTINGS`) drive the corridor doors straight from the
Raspberry Pi's hardware PWM instead of a PCA9685. Those motors move instantly, ignore
travel times, and have no `hold` option: their dialog shows no `Hold position`
checkbox, and only `open()` and `close()` are available.
```
