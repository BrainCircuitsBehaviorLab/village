## Task Examples (Raspberry Pi only)

Tasks with no external controller: the Raspberry Pi itself runs the trial (`BEHAVIOR_CONTROLLER` set to `OTHER`).

| File | What it shows |
| :--- | :--- |
| [raspberry_area1_sound.py](raspberry_area1_sound.md) | No controller: entering box area 1 plays a sound and lights an LED of the LED strip, reacted to in [camera_trigger.py](camera_trigger.md). |
| [raspberry_touchscreen.py](raspberry_touchscreen.md) | No controller: a menu of 6 rectangles on the touchscreen, each one showing a different stimulus when touched, reacted to in [touch_trigger.py](touch_trigger.md). |

```{toctree}
:hidden:
:maxdepth: 1

raspberry_area1_sound.md
raspberry_touchscreen.md
```
