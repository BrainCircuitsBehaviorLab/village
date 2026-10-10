## Task Examples (Bpod)

Tasks whose trials are run by a Bpod state machine (`BEHAVIOR_CONTROLLER` set to `BPOD`). Each page shows the state machine diagram of the task.

### Training stages

The six tasks of the [training protocol](training_protocol.md), in order.

| File | What it shows |
| :--- | :--- |
| [bpod_1_habituation.py](bpod_1_habituation.md) | Habituation to the box: one 60-second state per trial; pokes are only registered, no reward. |
| [bpod_2_passive.py](bpod_2_passive.md) | Passive learning: water is delivered as a side LED turns on, and then the animal is expected to poke that port. |
| [bpod_3_active.py](bpod_3_active.md) | Active learning: a side LED turns on, and water is delivered only after poking that port. |
| [bpod_4_center_initiated.py](bpod_4_center_initiated.md) | The animal starts each trial with a center poke; then only the lit side port is rewarded. |
| [bpod_5_introduce_penalty.py](bpod_5_introduce_penalty.md) | Like bpod_4_center_initiated, but a wrong-side poke gives a penalty sound and a time-out. |
| [bpod_6_delay.py](bpod_6_delay.md) | Poke the side that lights up first; the other side lights up after a random delay, which adapts to the animal's performance. |

### Other tasks, demos and tools

Not part of the training progression: they are run manually.

| File | What it shows |
| :--- | :--- |
| [bpod_area2_sound.py](bpod_area2_sound.md) | Driven by the box camera: entering box area 2 plays a sound and delivers water, through a Bpod softcode. |
| [bpod_touchscreen.py](bpod_touchscreen.md) | Touchscreen task: touching the rectangle that stays on screen gives water; touching the one that disappears sooner doesn't. |
| [bpod_example_global_timer.py](bpod_example_global_timer.md) | Demo, not a training task: a Bpod global timer bounding the whole trial. |
| [bpod_example_outputs_and_events.py](bpod_example_outputs_and_events.md) | Demo, not a training task: the Bpod primitives step by step — LEDs, valves, softcodes, TTL outputs and inputs. |
| [bpod_purge_ports.py](bpod_purge_ports.md) | Maintenance tool, not a training task: each valve stays open while its port is poked, to flush the water lines. |
