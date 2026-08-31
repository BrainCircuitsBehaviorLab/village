## Camera Calibration

Generates a printable symmetric circle grid and uses it to calibrate lens distortion
for the system cameras — the standard OpenCV checkerboard/grid calibration workflow,
adapted to a circle grid.

```{admonition} Note
:class: note
Always available.
```

### Calibrating

1. Print the generated circle grid (saved as `calibration_grid.pdf`) and mount it flat.
2. Hold it in front of the camera at different angles and distances while the panel
   detects the grid live and captures frames.
3. Once enough frames have been captured (at least 4), run the calibration. It
   computes the camera matrix and distortion coefficients in a background thread, so
   the panel stays responsive.

The panel reports the reprojection error (in pixels) and other diagnostics for the
result, so you can judge whether it's good enough before saving.

### Result

The result — camera matrix, distortion coefficients, reprojection error, image size,
number of frames used, and the grid spacing in mm — is saved as a JSON file. This
calibration is not applied automatically to the live camera feed; it is meant as a
reference (or to feed into your own undistortion/measurement code) rather than
something the core system consumes on its own.

---

Want to write your own calibration panel? See [Custom Calibrations](../advanced_customization/calibrations.md).
