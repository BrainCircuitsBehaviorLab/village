## Screen Integration

If you plan to present visual stimuli or record touch responses, enable the screen under
`SETTINGS` → `SCREEN SETTINGS`.

### Choosing the right screen technology

We recommend using an **infrared (IR) touch frame** rather than a capacitive touchscreen.
An IR frame works by projecting an invisible grid of IR beams across the display surface;
a touch event is registered whenever an object interrupts one of the beams. This means
the animal does not need to physically press the screen — proximity alone triggers a
response — which reduces aversion and improves task engagement for rodents.

The IR frame connects via USB and the display via the second micro-HDMI port on the
Raspberry Pi.

### Dual-screen configuration

The system runs with two display outputs:

- **HDMI-1**: Primary display showing the Training Village GUI *(can be virtual —
  no physical monitor required)*.
- **HDMI-2**: Secondary display inside the operant box showing behavioral stimuli.

To configure this, you need to tell the system to treat both HDMI ports as active,
regardless of whether a physical monitor is connected to HDMI-1.

**Step 1 — Edit the boot configuration:**

```bash
sudo nano /boot/firmware/cmdline.txt
```

Replace:

```
vc4.force_hotplug=1 video=HDMI-A-1:1600x900@60D
```

With:

```
vc4.force_hotplug=3 video=HDMI-A-1:1600x900@60D video=HDMI-A-2:1280x720@60D
```

The `vc4.force_hotplug` flag controls which HDMI ports the system treats as connected:
`1` = HDMI-1 only, `2` = HDMI-2 only, `3` = both. The `video=HDMI-A-*` parameters set
the resolution for each port independently.

**Step 2 — Set the resolution in the desktop:**

Navigate to **Raspberry Pi menu → Preferences → Control Centre → Screens → HDMI-2**,
set the resolution to **1280×720** or lower, and apply.

### Resolution and display latency

Keep the stimulus display at 1280×720 or below. Higher resolutions significantly
increase CPU load on the Raspberry Pi, which in turn increases stimulus presentation
latency.

The system operates at a **60 Hz refresh rate** (one frame every 16.6 ms). Because the
next frame is preloaded in the buffer while the current one is being displayed, the
latency from issuing a display command to the frame appearing on screen is typically
one full frame plus the remaining portion of the current frame. In practice, measured
latencies are **mean = 27.4 ms, SD = 7.5 ms**.

### Using the screen in tasks

Import the module-level instance, provide a drawing function, and call
`start_drawing()` / `stop_drawing()` to control when the stimulus appears.

**Displaying a static image:**

```python
from village.devices.screen import screen
from PyQt5.QtGui import QPainter

def draw():
    with QPainter(screen) as painter:
        if screen.image:
            painter.drawPixmap(0, 0, screen.image)

screen.load_draw_function(draw, image="stimulus.png")
screen.start_drawing()

# ... trial runs ...

screen.stop_drawing()
```

**Displaying a video:**

```python
def draw():
    frame = screen.get_video_frame()
    with QPainter(screen) as painter:
        if frame:
            painter.drawImage(0, 0, frame)

screen.load_draw_function(draw, video="movie.mp4")
screen.start_drawing()
```

**Drawing programmatically (shapes, text, time-varying stimuli):**

```python
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QColor, QPainter

def draw():
    with QPainter(screen) as painter:
        painter.fillRect(screen.rect(), QColor("black"))   # background
        # flash a white square for the first 0.1 s of each second
        if screen.elapsed_time % 1.0 < 0.1:
            painter.fillRect(QRect(100, 100, 200, 200), QColor("white"))

screen.load_draw_function(draw)
screen.start_drawing()
```

The drawing function is called once per frame (60 Hz) with no arguments. Two
attributes are updated automatically before each call:

- `screen.frame` — number of frames rendered since `start_drawing()`.
- `screen.elapsed_time` — seconds elapsed since `start_drawing()`.

Files passed to `image=` and `video=` are looked up inside `MEDIA_DIRECTORY`
(`/village_projects/<project_name>/media`). Reference them by filename only.

### Method reference

| Method | Arguments | Description |
|--------|-----------|-------------|
| `load_draw_function(draw_fn, image, video)` | `draw_fn`: callable; `image`, `video`: optional filenames | Sets the drawing function and pre-loads media. |
| `start_drawing()` | — | Starts the 60 Hz rendering loop. |
| `stop_drawing()` | — | Stops rendering and blanks the screen. |
| `load_image(file)` | `file`: filename | Loads an image from `MEDIA_DIRECTORY` into `screen.image`. |
| `load_video(file)` | `file`: filename | Prepares a video for playback (started by `start_drawing()`). |
| `get_video_frame()` | — | Returns the current video frame as a `QImage`, or `None`. |

---

### Configuring the touchscreen settings

Use these settings when the screen is configured as a touchscreen to both display stimuli and register touch responses from the animals.

Three settings control touchscreen behaviour:

| Setting | Description | Example |
|---|---|---|
| `TOUCHSCREEN_DEVICE` | Exact device name as shown in `/proc/bus/input/devices` | `USB Touch USB Touch` |
| `TOUCH_RESOLUTION` | Digitizer coordinate range: `[max_x + 1, max_y + 1]` | `[4096, 4096]` |
| `TOUCH_INTERVAL` | Minimum seconds between two registered touches (debounce) | `0.5` |

```{admonition} Note
:class: note
`TOUCH_RESOLUTION` is the internal coordinate range of the touch digitizer hardware —
it is independent of and usually different from the display pixel resolution.
The system uses both values to convert raw touch coordinates into screen pixel positions.
```

The device is looked up **by name** at startup, so the `/dev/input/eventX` path (which
can change after a reboot or USB reconnect) does not need to be configured.


#### Finding the device name and digitizer resolution

**Step 1 — List all input devices:**

```
cat /proc/bus/input/devices
```

Look for the entry that has `B: ABS` in its capabilities (indicating absolute position
events). The value you need is the `N: Name=` field:

```
I: Bus=0003 Vendor=0b1e Product=000f Version=0110
N: Name="USB Touch USB Touch"
...
H: Handlers=mouse0 event5
B: EV=1b
B: ABS=3
```

Copy the name exactly as it appears (without quotes) into `TOUCHSCREEN_DEVICE` (in this case `USB Touch USB Touch`).

**Step 2 — Find the digitizer resolution:**

Use the `Handlers` path from Step 1 (e.g. `event5`) to inspect the coordinate range:

```
sudo evtest /dev/input/event5
```

In the output, look for the `EV_ABS` section:

```
Event type 3 (EV_ABS)
  Event code 0 (ABS_X)
    Min        0
    Max     4095
  Event code 1 (ABS_Y)
    Min        0
    Max     4095
```

Set `TOUCH_RESOLUTION` to `[Max_X + 1, Max_Y + 1]` — in this example `[4096, 4096]`.

```{admonition} Note
:class: tip
If `evtest` is not installed: `sudo apt install evtest`
```
