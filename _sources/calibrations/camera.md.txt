## Camera Calibration

![Camera calibration screen](/_static/camera_calibration.webp)

The box camera uses a wide-angle lens, which distorts the image: straight lines look
curved, especially near the edges, and a centimetre does not cover the same number of
pixels in the centre of the image as in a corner. This panel measures that distortion
with a printed grid of dots, so that you can correct it in your analyses, for example
before converting the tracked positions of the animal into real distances. It also
measures how tilted the camera is with respect to a surface, which helps to align it.

Always available in the `CALIBRATION` screen. It calibrates the box camera; the
images of any other camera can be calibrated by loading them as files.

### How It Works

The grid is a sheet of black dots at a known, exact spacing. The calibration compares
where the dots really are (a perfect grid) with where the camera sees them, and works
out the lens model that explains the difference: the camera matrix (focal length and
optical centre) and the distortion coefficients. It uses the standard OpenCV
calibration (`calibrateCamera`), adapted to a grid of circles.

A single image is not enough, because the tilt of the sheet (perspective) and the
lens distortion look alike. With several images of the grid at different angles and
positions, the two can be separated. Dots are used instead of the classic chessboard
because the centre of a circle can be located with sub-pixel precision even in a
slightly blurred image. The white crosses inside the dots and the grey lines between
them are not used by the detection: they help to measure the sheet with a ruler and to
align several sheets.

### Panel Fields

The fields keep their values: each one is saved in a hidden setting
(`CAMERA_CALIBRATION_...`) as soon as it holds a valid value, so the panel opens with
the last values used.

**`GRID GENERATION`**: the printable grid.

| Field | Default | Description |
|---|---|---|
| `PAGE W (mm)` | 210 | Page width (A4). |
| `PAGE H (mm)` | 297 | Page height (A4). |
| `SPACING (mm)` | 50 | Centre-to-centre distance between dots. It is also the real spacing used to calibrate. |
| `DOT RADIUS (mm)` | 10 | Radius of each dot. |
| `MARGIN (mm)` | 15 | Empty border around the grid. With at least the dot radius all dots are complete; with `0` the dots on the edges are cut, to join several sheets. |

**`CALIBRATION DETECTION`**: the grid in front of the camera.

| Field | Default | Description |
|---|---|---|
| `GRID COLS` | 4 | Columns of dots to detect. Filled in when the PDF is generated. |
| `GRID ROWS` | 6 | Rows of dots to detect. Filled in when the PDF is generated. |
| `SPACING (px)` | blank | Expected spacing between dots in the image, in pixels. It restricts the detection to dots of that size; blank accepts dots of any usual size. |
| `MEASURED SPACING (mm)` | blank | Spacing measured on the printed sheet with a ruler. Only used for the px/cm heatmap; blank uses `SPACING (mm)`. |

The fields are read on every capture, so they can be changed between captures.

### Preparing the Grid

1. Press `GENERATE GRID PDF`. The grid is saved as `calibration_grid.pdf` in the
   project's `data` folder, and `GRID COLS` and `GRID ROWS` are filled in with its size:
   4 x 6 dots with the default values.
2. Print it at 100% scale, not "fit to page", on matte paper (glossy paper can reflect
   the light and hide dots).
3. Check the spacing with a ruler. If it is not exactly the one requested, enter the real
   value in `MEASURED SPACING (mm)`. Only the px/cm heatmap depends on it: the lens
   distortion does not depend on the size of the grid.
4. Mount it flat on a rigid surface, such as a piece of cardboard or a board.

To cover a larger area, for example the whole floor of the box, build a bigger grid
from several sheets: set `MARGIN (mm)` to `0`, so that the dots on the left and bottom
edges of each sheet are cut in half and are completed by the next sheet when the sheets
overlap. Use the grey lines to align them, and enter the total number of dots of the
assembled grid in `GRID COLS` and `GRID ROWS`.

### Capturing Frames

1. Hold the grid in front of the box camera, with all its dots visible, and press
   `CAPTURE FRAME`. The detected grid is drawn on the preview for 2 seconds, and then
   the preview goes back to the live image.
2. Repeat with the grid at different positions, distances and angles. Cover the
   whole image, including the corners and edges, where the distortion is larger, and
   tilt the sheet in different directions.
3. From the fourth frame on, each capture runs the calibration with all the frames
   captured so far, in the background. More frames give a more reliable result: 10 to
   15 well distributed frames are a good target.

`LOAD IMAGE` uses an image file as a frame instead of the live camera, and
`CLEAR FRAMES` discards all the frames to start over. All the frames of a calibration
must have the same size. The frames are discarded when you leave the `CALIBRATION`
screen; save the result before leaving.

If the grid is not detected:

- Check that `GRID COLS` and `GRID ROWS` match your grid, and that all its dots are
  visible and in focus.
- Leave `SPACING (px)` blank: a wrong value makes the detector reject the dots.
- Avoid reflections and strong shadows on the sheet.

```{admonition} Top of the image
:class: note
The frames include the status bar that the camera draws at the top of the image
(about 1/12 of its height), so the dots under it are not detected. Keep the grid
below it.
```

### Reading the Results

After each calibration the panel shows:

- **Calib reproj error**: the mean distance, in pixels, between the detected dots and
  where the calibrated model places them. Below 1 px is good; with good frames it is
  usually between 0.1 and 0.5 px. A high value usually means blurred or badly detected
  frames: clear them and capture new ones.
- **Distortion**: the type and strength of the radial distortion, from `k1`. Negative
  is barrel distortion (edges bulging outwards, typical of wide-angle lenses), positive
  is pincushion.
- **k1, k2, p1, p2**: the distortion coefficients. `k` are radial and `p` tangential
  (a lens not exactly parallel to the sensor); `p` are usually close to zero.
- **Principal pt offset**: how far the optical centre is from the centre of the image.

Once there is a result, each new capture also shows **Physical adjustment**: the tilt
(left/right and front/back) and the roll of the grid with respect to the camera, with
hints such as "raise right". The tilt is rated `GOOD` below 2° and `OK` below 5°, and
the roll `GOOD` below 1° and `OK` below 3°; anything else is `POOR`. To
check that the camera looks straight down at the floor of the box, lay the grid flat on
the floor and adjust the camera until the tilt is `GOOD`.

The four plots on the right show:

- **Residual error**: the reprojection error of every dot used. If it is concentrated
  in one area, capture more frames there.
- **Lens distortion field**: how much, and in which direction, each part of the image
  moves when the distortion is corrected.
- **Tilt and roll**: the shape of the grid in the last frame (red) compared with the
  same grid seen straight on (green).
- **px/cm**: how many pixels a centimetre covers across the grid in the last frame.

### Result

`SAVE JSON` saves the result as `camera_calibration.json` in `data/<SYSTEM_NAME>/`,
next to the other calibrations of the system, replacing the previous one. Besides the lens model, it records everything
needed to understand the calibration later, even if the panel's values change
afterwards:

| Field | Description |
|---|---|
| `date`, `system_name`, `village_version` | When, on which system and with which version of Village it was made. |
| `camera_matrix` | `[[fx, 0, cx], [0, fy, cy], [0, 0, 1]]`, in pixels: focal lengths and optical centre. |
| `dist_coeffs` | `[k1, k2, p1, p2, k3]`: the distortion coefficients, in OpenCV order. |
| `reprojection_error_px` | The mean reprojection error, in pixels. |
| `image_size_wh` | Size of the calibrated frames. The calibration is only valid at this resolution. |
| `n_images_used` | Number of frames used. |
| `spacing_mm`, `measured_spacing_mm`, `spacing_px` | The grid and detector values (`null` when blank). |
| `frames` | Every frame used: its source (the box camera, with its resolution and lens position, or an image file), the grid size, the spacing and the number of dots found. |
| `description` | What each of these fields means. |

### Using the Calibration

The calibration is not applied automatically: the camera, the tracking and the videos
keep working with the original image. Use it in your own analyses, for example to
correct the positions of the animal saved in the CSV file of each video. The positions
must come from a video recorded at the resolution in `image_size_wh`.

```python
import json

import cv2
import numpy as np
import pandas as pd

with open("data/my_system/camera_calibration.json") as f:  # data/<SYSTEM_NAME>/
    calibration = json.load(f)
K = np.array(calibration["camera_matrix"])
dist = np.array(calibration["dist_coeffs"])

frames = pd.read_csv("video.csv", sep=";")
tracked = frames[(frames["x_position"] >= 0) & (frames["y_position"] >= 0)]
points = tracked[["x_position", "y_position"]].to_numpy(np.float32)

# positions as they would be seen through a lens without distortion, in pixels
corrected = cv2.undistortPoints(points.reshape(-1, 1, 2), K, dist, P=K).reshape(-1, 2)
```

To correct whole images, use `cv2.undistort(image, K, dist)`.

---

Want to write your own calibration panel? See [Custom Calibrations](../advanced_customization/calibrations.md) and the [led_calibration.py](../examples/led_calibration.md) example.
