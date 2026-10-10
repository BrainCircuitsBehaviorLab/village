## Camera, Touchscreen, GPIO & Scale

Code that reacts, while a task is running, to the box camera, the touchscreen, the GPIO input pin or the box scale.

| Page | What it covers |
| :--- | :--- |
| [Custom Camera Interaction](../protocols/camera.md) | Reacting to the animal's position in the box camera areas, and drawing on the camera image. |
| [Custom Touchscreen Interaction](../protocols/touchscreen.md) | Reacting to touches on the touchscreen. |
| [Custom GPIO Interaction](../protocols/gpio_trigger.md) | Reacting to the GPIO input pin going ON and OFF. |
| [Custom Scale Interaction](../protocols/scale_trigger.md) | Reacting to the weight read by the box scale. |

Example files:

| File | What it shows |
| :--- | :--- |
| [camera_trigger.py](camera_trigger.md) | Reacts to the box camera areas, for [bpod_area2_sound.py](bpod_area2_sound.md) and [raspberry_area1_sound.py](raspberry_area1_sound.md). |
| [touch_trigger.py](touch_trigger.md) | Reacts to the touchscreen touches, for [bpod_touchscreen.py](bpod_touchscreen.md) and [raspberry_touchscreen.py](raspberry_touchscreen.md). |
| [gpio_trigger.py](gpio_trigger.md) | Records the input pin (`GPIO_IN`) as `GpioOn`/`GpioOff` events in the trial data of any running task. |
| [scale_trigger.py](scale_trigger.md) | Records when the animal steps on and off the box scale as `ScaleOn`/`ScaleOff` events in the trial data of any running task. |

```{toctree}
:hidden:
:maxdepth: 1

../protocols/camera.md
../protocols/touchscreen.md
../protocols/gpio_trigger.md
../protocols/scale_trigger.md
camera_trigger.md
touch_trigger.md
gpio_trigger.md
scale_trigger.md
```
