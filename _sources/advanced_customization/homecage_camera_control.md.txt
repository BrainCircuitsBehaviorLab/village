## Homecage Camera Control

Some setups connect two homecages through the corridor, with animals able to move
between them. `AREA_EXTRA` is a 5th, special corridor detection area (on top of the
regular `AREA1_CORRIDOR`-`AREA4_CORRIDOR`) used to check that the passage between the
two homecages isn't physically blocked (e.g. by bedding, an animal staying put for
hours, or a mechanical issue) for longer than expected.

It's off by default, and everything about it is opt-in.

---

### Enabling it

In `SETTINGS` -> `ADVANCED SETTINGS`, turn `CORRIDOR_AREA_EXTRA` ON. This reveals a
second setting, `AREA_EXTRA_HOURS`: the size, in hours, of the window used to decide
whether the passage has been blocked for "too long" (see [Occupation alarm](#occupation-alarm)
below).

```{admonition} Note
:class: note
Like the other corridor/box camera options, `CORRIDOR_AREA_EXTRA` takes effect for the
`MONITOR` tab described next after restarting the app.
```

---

### Configuring the area

Once active, a new `EXTRA` tab appears in `MONITOR`, alongside `INFO`, `PLOT` and
`DETECTION SETTINGS`. It shows:

- **`empty limit`** — same idea as the `DETECTION SETTINGS` tab's mouse-detection
  limits, but only the empty/not-empty threshold: this area only cares about whether
  the passage is blocked, not how many subjects are in it, so there's no
  `subject limit` control here.
- **`View detection corridor`** — the same `VIEW_DETECTION_CORRIDOR` toggle already in
  `DETECTION SETTINGS` (changing it here changes it everywhere; it's just exposed in
  both places for convenience).
- **`AREA_EXTRA_CORRIDOR`** position and threshold controls — `left`, `right`, `top`,
  `bottom`, and day/night detection thresholds, exactly like `AREA1_CORRIDOR`-`AREA4_CORRIDOR`
  in `DETECTION SETTINGS`. Position the rectangle over the passage between the two
  homecages.

When active, the area is drawn on the corridor camera feed in a vivid violet
rectangle (`COLOR_EXTRA`, editable in `SETTINGS` -> `ADVANCED SETTINGS` -> `VISUAL
SETTINGS`, alongside `COLOR_AREA1`-`COLOR_AREA4`, once `CORRIDOR_AREA_EXTRA` is ON) —
deliberately different from the 4 regular areas' colors, so it stands out against any
background.

---

### Occupation alarm

While `AREA_EXTRA` is active, every camera frame is checked: if the area's detected
pixel count is above `empty limit`, that frame counts as "occupied" (blocked). Once
every `AREA_EXTRA_HOURS` hours, the system checks what fraction of frames during that
window were occupied — if more than 90%, it raises a repeating alarm:

> Communication between homecages has been closed for more than *N* hours

The alarm repeats (like other repeating alarms) until acknowledged, either from the
Telegram button or the `ALARM` button in the GUI. The occupied/total frame counters
then reset and a new `AREA_EXTRA_HOURS` window starts.

```{admonition} Note
:class: note
This is independent from `CORRIDOR_OCCUPATION_ALARM` (areas 1-4's own >90%-of-the-last-hour
check) -- `AREA_EXTRA` always uses its own window length (`AREA_EXTRA_HOURS`), not the
fixed 1 hour used for the other 4 areas.
```
