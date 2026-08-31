## Corridor Threshold Calibration

Lets you position the four corridor detection areas and tune their day/night
pixel-detection thresholds while previewing the result against a recorded corridor
video, instead of tuning blind or waiting for an animal to be live in the corridor.

```{admonition} Note
:class: note
Only available when `USE_CORRIDOR` is **ON**.
```

### Workflow

1. Load a day video and/or a night video recorded from the corridor camera.
2. The panel scans each video and, for every one of the 4 areas, tries to find a frame
   where the animal is alone in that area — giving you a realistic preview to tune
   against instead of an empty corridor.
3. Adjust each area's position (`left`/`right`/`top`/`bottom`) and its day/night
   threshold (`thr_day`/`thr_night`) with the same +/- controls used in the MONITOR
   tab — changes write directly to the real `AREA1_CORRIDOR`..`AREA4_CORRIDOR`
   settings and the preview updates live, so what you tune here is exactly what the
   corridor camera will use.

```{admonition} Note
:class: note
There is no separate "apply" step — this panel edits the same settings the corridor
camera reads from, live. Re-scanning (e.g. after loading a different video) re-picks
the preview frames but does not change any threshold or position value.
```

---

Want to write your own calibration panel? See [Custom Calibrations](../advanced_customization/calibrations.md).
