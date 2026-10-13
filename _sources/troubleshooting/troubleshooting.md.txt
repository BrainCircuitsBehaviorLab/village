## Troubleshooting Guide

The Training Village is a multi-component system where hardware, software, and behavior intersect. Minor miscalibrations or component failures can lead to suboptimal performance. Typically, small issues may arise during the first few days of deployment as the animals habituate and the sensors are fine-tuned.

When a system anomaly is detected, an automated alert is instantly dispatched via Telegram. It is crucial to respond promptly by logging in remotely to investigate the root cause of the error, reviewing the corridor and operant box video recordings. For example: a door that does not close properly or a lighting failure can produce several types of errors: incorrect RFID detection, two animals simultaneously entering the operant box, the system registering an animal as present when the box is empty, or the system failing to detect an animal that is actually inside.

---

### Where to Look First

- **The events log** (`DATA` → `EVENTS`): every action, refusal and error is written
  there. Double-click a row to see its full description and, for errors, the Python
  traceback with the line of code that failed.
- **The videos**: select an event and click `VIDEO` to see the corridor at that moment,
  or open the session video from `DATA` → `SESSIONS_SUMMARY`.
- **The terminal** where `village` was launched, which also shows the messages printed
  by your own code.
- **The logs of the synchronization and of the video deletion** (`rsync_logs/` and
  `data_removal_logs/`, in `data/<SYSTEM_NAME>/`).


---

### Illumination & Tracking Issues

Many gating or tracking failures are not caused by software bugs, but by physical lighting conditions.

#### Symptom: Double Entries or Wrong RFID detections
If you notice that two animals are entering the operant box simultaneously, or that a gate closes while an animal is still in the corridor, the cause is usually **optical reflections**.
* **The Cause:** The computer vision algorithm relies on a clean binarized pixel count. If there are glare reflections on the clear acrylic corridor ceiling, the camera can become "blind" to those reflection zones. For example, if a second animal is standing directly under a heavy glare reflection, its pixels will not be counted. The system will assume the corridor is empty and mistakenly open the gate for an RFID-tagged animal, leading to double entries or wrong RFID detections.
* **The Solution:** Adjust the physical positioning or angles of your external room lights. Ensure the corridor is shielded from direct overhead glare. While the camera automatically adjusts its exposure between day (`VISIBLE`) and night (`IR`) modes to keep images consistent, it cannot filter out localized mirror-like reflections on plastic surfaces.

#### Symptom: Broken Video-Tracking inside the Operant Box
If the advanced center-of-mass tracking (`findContours`) is dropping or jumping erratically inside the behavioral arena, inspect the box illumination profile.
* **The Cause:** The operant box tracking requires highly uniform illumination (either visible or IR, depending on your paradigm).
* **The Solution:** Ensure the LED strips inside the box are clean and fully functional. **Never open the operant box door while a behavioral session is actively running**, as the sudden influx of external room light will completely disrupt the binarization thresholds and crash the real-time tracking loop.

---

### Camera Issues (Connection Error or Malfunctioning)

1. **Verify Physical Connections:** Ensure both camera ribbon cables are firmly seated in the Raspberry Pi 5 MIPI CSI slots and that the white locking clips are fully engaged.
2. **Check Camera Indices:** Open the application GUI, navigate to `SETTINGS` → `CAMERA SETTINGS`, and verify that your camera indices are properly assigned (typically one is `0` and the other is `1`).
   * `CAM_CORRIDOR_INDEX`: `0` or `1`
   * `CAM_BOX_INDEX`: `0` or `1`
3. **Reboot:** If you swapped indices or re-seated the cables, restart the system to allow the OS to re-initialize the video devices.

---

### Controller Issues (Bpod or Arduino Connection Error)

1. **Verify Physical Port:** Ensure your behavioral controller is plugged into the **bottom USB 3.0 port** (the bottom blue port closest to the Raspberry Pi’s onboard Ethernet connector).
2. **Verify App Settings:** Navigate to `SETTINGS` → `CONTROLLER SETTINGS` in the GUI. Ensure your specific controller type is selected and the device path is set exactly to `/dev/controller`.
3. **Check System Devices:** Open a terminal and check if Linux detects the hardware as a raw serial interface by running:
```
ls /dev/ttyACM* /dev/ttyUSB*
```
4. **Isolate Hardware**: If no device appears in step 3, try replacing the USB cable. Use a shorter, high-quality, shielded USB cable to prevent electromagnetic interference.
5. **Verify Symbolic Link**: Check if the automated udev rule successfully generated your symlink by running:
```
ls -l /dev/controller
```
6. **Fix Missing Symlink:** If the raw device (`ttyACM*` or `ttyUSB*`) appears but `/dev/controller` is missing, inspect the system logs by typing `dmesg` to find the exact port configuration, then review your rule file at `/etc/udev/rules.d/99-usb.rules`.

```{admonition} Understanding Symlinks, udev Rules & /dev/controller
:class: note
A **symlink** (short for symbolic link) is a software shortcut in Linux that transparently redirects one file path to another.

* **Why it is necessary:** When you connect a serial device (like a Bpod or Arduino) to the Raspberry Pi, Linux dynamically assigns it a generic node path like `/dev/ttyACM0` or `/dev/ttyUSB0`. However, if the device is unplugged, if the Pi reboots, or if another USB peripheral is connected, Linux might randomly reassign that hardware to `/dev/ttyACM1`. If the Training Village software were hardcoded to look for a static name like `ttyACM0`, the connection would instantly break.
* **The Automated Solution (`udev` rules):** To prevent this, Linux uses a background device manager called `udev`. The Training Village comes pre-configured with a custom rule file (located at `/etc/udev/rules.d/99-usb.rules`) containing the following instruction: `SUBSYSTEM=="tty", KERNELS=="1-1:1.0", SYMLINK+="controller"`

* **How this udev rule works:** `SUBSYSTEM=="tty"`: Filters the incoming hardware events and tells Linux to only trigger this rule if the connected device is a serial/terminal interface (like a USB microcontroller). `KERNELS=="1-1:1.0"`: instead of looking at what device is plugged in, it looks at where it is plugged in. `1-1:1.0` corresponds to the exact physical address of the bottom USB port adjacent to the Raspberry Pi 5 Ethernet jack. `SYMLINK+="controller"`: If a serial device matches the criteria above, udev automatically creates a permanent, unchangeable symbolic link shortcut named /dev/controller pointing straight to it.

Thanks to this rule, no matter what microcontroller you plug into that specific bottom port, and regardless of the generic name Linux gives it internally, the Training Village software can always find your behavioral controller seamlessly.

```

---

### Peripheral Issues (Sensors, Motors, Lights, or Satellite Boards)

1. **Verify Software Activation:** Open the GUI and ensure the specific satellite board you are trying to communicate with is enabled: toggle `USE_CORRIDOR` (top of `SETTINGS` → `CORRIDOR SETTINGS`) or `USE_BOX_BOARD` (top of `SETTINGS` → `BOX SETTINGS`) to **`ON`** depending on your active setup.
2. **Verify Satellite Connections:** Check that the failing component (servo, LED strip, RFID antenna) is securely connected to the correct ports on the Corridor Board or Box Board with the correct wiring polarity.
3. **Check Hub-to-Satellite Cables:** Each satellite board is linked by two cables — an Ethernet cable carrying data, and a separate power cable (DC barrel jack on both ends) carrying 5V. Ensure both are firmly plugged into their respective dedicated ports on the Main HAT.
4. **Check HAT Seating:** Ensure the Main HAT is fully pressed down and evenly seated onto the Raspberry Pi 5 GPIO header extension pins.
5. **Test Power Lines:** Verify that the Main HAT is receiving a stable **5V (3A)** from the 5V power supply. A drop in voltage can cause I2C chips, scales, or servos to drop off the bus randomly.
6. **Restart Village After Reconnecting a Motor:** Physically unplugging and replugging a servo can momentarily glitch the power rail feeding its PWM driver chip (PCA9685), resetting the chip's internal PWM frequency configuration. The Raspberry Pi's I2C connection to the chip keeps working (no error is shown), but the servo stops responding correctly because the pulse timing it's now receiving no longer matches what it expects. That frequency is only configured once, when Village starts — if a motor stops working after being disconnected and reconnected, **restart Village** to reinitialize it, rather than assuming the servo itself is broken.


---

### An Animal Never Enters the Box

When an animal is detected by the RFID reader but not let in, the reason is written in
the events log. Check, in this order:

1. **The RFID reader is ON** (`MONITOR` → `CORRIDOR`), and the tag is being read: every
   reading writes "Tag detected: …" in the events.
2. **The subject is registered with that tag.** Otherwise the events show "Subject with
   tag: … not found" (see [Subject Management](../system_operation/subject.md)).
3. **The subject is active now.** "Subject not active" means its `active` field is OFF
   or the current hour is outside its schedule.
4. **Its refractory period is over.** "Subject not allowed to enter until …" shows its
   `next_session_time`, which is the end of its last session plus `refractory_period`.
5. **The corridor looks right to the camera.** "Detection in area1: …", "Detection in
   area2: …" or "Large detection in area3: …" mean that, for the camera, there is
   something else in the corridor or two animals in area 3. Check the lighting, dirt and
   the thresholds (see [Animal Detection & Tracking](../system_operation/detection.md)).
6. **Only one tag was read.** "Multiple tags detected in the last seconds" means another
   animal was detected less than `TIME_BETWEEN_DETECTIONS` seconds before.

The corridor camera must also be giving an image: without it, no animal is let in.

---

### Errors at Startup or When Launching a Task

- **"System running in debug mode"** when Village starts: a device could not be
  started. The message lists which ones; see the sections above for cameras, the
  controller and the peripherals.
- **"Couldn't import <file>"** in the events: a Python file of your `code` folder has an
  error. Double-click the row to see the traceback. Everything in that file (tasks,
  triggers, plots...) is ignored until it is fixed. "No tasks could be imported" and
  "Training protocol not found" usually come from the same cause.
- **"Error running task: … not found"**: the subject's `next_task` names a task that
  doesn't exist (renamed or deleted). Fix the training protocol, or the subject's
  `next_settings` in the `SUBJECTS` screen.
- **"WATER CALIBRATION PROBLEM" / "SOUND CALIBRATION PROBLEM"** when a task starts: the
  task asked for a volume or a sound level that is not calibrated, or out of the
  calibrated range. Calibrate it (see [Water Calibration](../calibrations/water.md) and
  [Sound Calibration](../calibrations/sound.md)), or change the requested value.
- **"Error running task …"** while the task runs: an exception in the task code. The
  traceback shows the line.

---

### The Animal Doesn't Leave (Scale and Exit Detection)

The system decides that the animal has gone back home by combining the corridor camera
and the corridor scale. With door 2 open, it waits until areas 3 and 4 are empty, the
animal is in area 2, and the scale gives a stable weight between
`MIN_WEIGHT_THRESHOLD` and `MAX_WEIGHT_THRESHOLD` (10 to 40 g by default, in
`SETTINGS` → `CORRIDOR SETTINGS`). Only then it closes door 2, opens door 1 and writes
"Subject back home: … g".

If the scale is not working, is badly calibrated, or the thresholds don't fit your
animals, the system keeps waiting. Once the task has reached its `maximum_duration`,
if the animal is still not detected back home one hour later, it sends "The subject
has been in the box for too long." (repeated every hour).

- **Check the scale** from `MONITOR` → `CORRIDOR`: `TARE SCALE` with nothing on it, then
  `GET WEIGHT` with a known weight. If it is wrong, `CALIBRATE SCALE` again.
- **Check the thresholds** against the weight of your animals. For rats, or for heavier
  mice, `MAX_WEIGHT_THRESHOLD` must be raised.
- **If an animal is stuck**, help it out and use `CHANGE STATE` → "All subjects are
  back home, go to WAIT state" (see [Toolbar Controls](../system_operation/toolbar.md)).

---

### After a Power Cut

The Raspberry Pi starts again by itself when the power comes back, but **the Training
Village does not**: it has to be launched again (`village`, see
[Launching the TV Application](../preparation/launching.md)). Until then, no animal can
enter the box, and the healthchecks.io heartbeat stays silent, so the team gets the
heartbeat alarm.

1. **Before launching it, save the interrupted session if you need it.** While a session
   runs, its events are written as they happen to `data/sessions/session.csv`, and the
   session files are only created when the session ends. That file is emptied when the
   Training Village starts, so copy it somewhere else first. The interrupted session is
   not added to the subject's data, and its settings are not updated.
2. **Launch the Training Village.** It starts in `WAIT`, without moving the doors.
3. **Check, with the box camera, whether an animal was left inside.** If so, open door 2
   from `MONITOR` → `CORRIDOR` so that it can leave, and when it is back home leave door
   1 open and door 2 closed.
4. Check that the cameras, the RFID reader and the Telegram bot work again, as after any
   start.

---

### No Sound

- **The DAC is still used by the operating system.** Its device profile must be set to
  **Off** (see [Sound Integration](../system_operation/sound.md)).
- **The sound device is not selected**: `SETTINGS` → `SOUND SETTINGS` → `USE_SOUNDCARD`
  ON, and the right `SOUND_DEVICE`.
- **The sound card mutes itself** after a silence: disable its auto-mute (see the
  [manual installation](../resources/software_installation.md)).
- **"Error in sound device"** in the events: double-click it to see the cause.

---

### Screen or Touchscreen Issues

- **Nothing is shown on the screen of the box**: the system must be set to always detect
  two screens (`vc4.force_hotplug=3` in `/boot/firmware/cmdline.txt`), and the second
  screen must be connected to the second micro-HDMI port (see
  [Screen Integration](../system_operation/screen.md)).
- **Touches are not registered**: check `TOUCHSCREEN_DEVICE` (the exact name of the
  device) and `TOUCH_RESOLUTION`.
- **Touches move the mouse pointer of the desktop**: the udev rule that tells the desktop
  to ignore the touchscreen is missing (see [Screen Integration](../system_operation/screen.md)).

---

### The RFID Reader Doesn't Read

- **Check the wiring of the reader** (the connector order of the ID-20LA, see the
  [Assembly Guide](../resources/hardware.md)) and that the Corridor Board is powered.
- **The serial port must be enabled** (`enable_uart=1`, see the
  [manual installation](../resources/software_installation.md); already done in the
  disk image).
- **Check the chip**: hold the animal over the reader. A chip that is too deep or badly
  oriented may only be read from some positions.

---

### Remote Access or Telegram Bot Not Responding

- **Remote access is lost but the bot answers**: send `/restart_anydesk` or
  `/restart_vnc` (see [Alarm System Overview](alarm.md)).
- **The bot doesn't answer anything**: either the Training Village is not running, or
  the Raspberry Pi has no internet connection. This is the same situation as the
  heartbeat alarm.
- **The bot never answered**: check `TELEGRAM_TOKEN` and `TELEGRAM_CHAT` (see
  [Telegram Bot Integration](../preparation/telegram.md)).

---

### After Updating the Training Village

If, after a `git pull`, the Training Village fails to start because a Python module
can't be imported, the new version needs a new dependency. Install it inside the
Python environment:

```
source ~/.env/bin/activate
cd ~/village
pip install -e . --config-settings editable_mode=compat
```

---

### Data Synchronization Issues

If you suspect a transfer issue, you can inspect the detailed synchronization logs generated by the system. The log files are stored locally in the following directory:

`/home/pi/village_projects/YOUR_PROJECT/data/YOUR_SYSTEM/rsync_logs`

If the synchronization fails for 24 hours, the system sends the alarm "No data sync in
the last 24 hours." to your team's Telegram group chat (see
[Alarm System Overview](alarm.md)). Review the logs inside the `rsync_logs` folder to
identify the specific transfer error, and verify your network connectivity or remote
storage availability.
