## Saved Data and Video

The Training Village automatically handles all aspects of data collection, including raw
and processed behavioral datasets, video recordings, video-tracking coordinates, and
system metrics.

---

### Directory Hierarchy & Folder Structure

The `village_projects/` directory is structured as follows:

```text
village_projects/
└── projectName/
    ├── code/
    ├── media/
    └── data/
```

A dedicated folder is created for each project using the specified project name. Each
project contains three subdirectories:

- **`code/`**: Stores all executable Python source code and experiment-specific scripts.
  See the [PROTOCOL & TASK DESIGN][CREATE] section for a detailed breakdown.
- **`media/`**: *(Optional)* Stores audio tracks, videos, or image assets required by
  behavioral tasks.
- **`data/`**: Central repository for all experimental outputs, including raw and
  processed data files and videos.

---

### Inside the Data Folder

```text
data/
├── sessions/
├── videos/
└── systemName/
```

- **`sessions/`**: Contains one subfolder per animal with raw and parsed session datasets.
- **`videos/`**: Contains one subfolder per animal with video recordings.
- **`systemName/`**: Named after your system ID; contains platform-wide metrics and
  hardware logs.

---

### System Configuration Folder (`systemName/`)

```text
systemName/
├── rsync_logs/
├── data_removal_logs/
├── old_events/
├── events.csv
├── subjects.csv
├── sessions_summary.csv
├── temperatures.csv
├── active_history.csv
├── deleted_sessions.csv
├── water_calibration.csv
└── sound_calibration.csv
```

#### Core Data Files

- **`events.csv`**: Log of all system events. Columns: `date`, `type`, `subject`,
  `description`.

- **`subjects.csv`**: Table with one row per subject, used to track the settings that
  will be applied in each subject's next session. Columns: `name`, `tag`,
  `basal_weight`, `active`, `next_session_time`, `next_settings`.
  The `next_settings` field is a JSON string containing the parameters computed for the
  upcoming session, including `next_task` and `refractory_period`. The
  `next_session_time` field indicates the earliest time at which the subject is eligible
  for another session; it is calculated by adding `refractory_period` to the end time of
  the previous session.

- **`sessions_summary.csv`**: Summary table of all completed sessions. A new row is
  appended each time a session ends. Columns: `date`, `subject`, `tag`, `weight`,
  `task`, `duration`, `trials`, `water`, `settings`.

  ```{admonition} Note
  :class: warning
  For the `water` column to be populated, water intake must be explicitly recorded within
  the task definition (see [PROTOCOL & TASK DESIGN][CREATE]).
  ```

#### Other Data Files

- **`temperatures.csv`**: Hourly temperature and humidity log, recorded automatically.
  Columns: `date`, `temperature`, `humidity`.

- **`active_history.csv`**: Log of every change to a subject's `active` schedule
  (ON/OFF/hours), so that past activity plots use the schedule each subject actually had
  at each moment.

- **Calibration files** (`water_calibration.csv`, `sound_calibration.csv`, and one per
  custom calibration, e.g. `led_calibration.csv`): every measurement saved by each
  calibration. Their values can be retrieved and used within tasks (see
  [Calibrations](../calibrations/overview.md)).

- **`deleted_sessions.csv`**: List of manually deleted sessions.

  ```{admonition} Important
  :class: warning
  Deleting a session never removes the underlying data — it simply adds an entry to this
  list, causing the session to be excluded from `sessions_summary.csv` and from the
  per-subject global session file.
  ```

#### Log Folders

- **`rsync_logs/`**: Log of every data synchronization and backup attempt with a remote
  server or external drive, regardless of whether it succeeded or failed.
- **`data_removal_logs/`**: Log of the deletion process for videos that have already been
  synchronized to a remote server or external drive.
- **`old_events/`**: To prevent `events.csv` from growing too large, a new file is
  created once a line threshold is exceeded. Older event records are archived here.

---

### Subject Behavioral Sessions

- **Storage path:** `data/sessions/{subject}/`
- **Filename format:** `{subject}_{task}_{timestamp}`

Three files are generated for every completed behavioral session:

```text
data/sessions/{subject}/
├── {filename}_RAW.csv
├── {filename}.csv
└── {filename}.json
```

#### 1. Raw Session (`{filename}_RAW.csv`)

One row per event. During the session, the events are written as they happen to
`data/sessions/session.csv`; when the session ends, that file is copied here.

| Column | Description |
| :--- | :--- |
| `TRIAL` | Trial index. |
| `START` | Absolute Unix timestamp (4 decimal places) marking the onset of a state or event. |
| `END` | Absolute Unix timestamp of state termination (empty for instantaneous events). |
| `MSG` | Message type (see standards below). |
| `VALUE` | Value associated with the message. |

**Message type standards (`MSG`):**

- `_Transition_to_{stateName}`: State machine transition flag.
- `STATE_{stateName}_START` / `STATE_{stateName}_END`: Structural boundaries of a
  behavioral state.
- *Hardware event name*: Digital input/output line transitions (e.g., photo-gate beams,
  ports).
- *Custom variable tag*: Any performance variable explicitly captured with
  `register_value()` (e.g., `stimulus_side`, `correct_choice`, `rewarded`). The tag name
  is written to `MSG` and its value to `VALUE`.
- `TRIAL_START` / `TRIAL_END`: Absolute trial boundary markers.

#### 2. Processed Session (`{filename}.csv`)

A parsed, trial-by-trial overview: instead of one row per event, this file contains one
row per trial. Each row is built when its trial finishes (after `after_trial`), and the
file is saved when the session ends. It begins
with the following fixed columns: `session`, `date`, `trial`, `subject`, `task`,
`system_name`, `run_mode`.

```{admonition} run_mode
:class: note
The `run_mode` field is set to `Manual` if the session was launched manually from the
GUI, or `Auto` if it was triggered automatically upon detecting an animal in the corridor.
```

#### 3. Session Settings Metadata (`{filename}.json`)

Stores all parameters used during the session: `minimum_duration`, `maximum_duration`,
`run_mode`, `observations`, and all custom protocol parameters.

To add a note to a session, click on its entry in `sessions_summary` within the GUI. A
panel listing all session parameters will appear; the `observations` field is editable
and empty by default.

```{admonition} Tip
:class: note
Although `.json` files already capture all parameters used in a session, it is good
practice to also record relevant variables from within the task using `register_value()`,
as this makes them directly accessible in the `.csv` file.
```

#### Aggregate History File

In addition to the per-session files, a persistent history file is maintained in each
subject's directory:

- **`{subject}.csv`**: Compiles every historical session completed by that animal. New session rows are appended each time a session ends. This aggregate dataset is essential for adaptive automated training (`training_protocol.py`), allowing the system to evaluate progression milestones — for example, verifying whether an animal achieved >80% accuracy over its last three sessions before advancing to the next training stage.

---

### Video Recordings & Frame Data

Every recording produces two files with the same name: an `.mp4` video (H.264) and a
`.csv` table with one row per frame.

#### Box Videos (one per session)

- **Storage path:** `data/videos/{subject}/`
- **Filename format:** `{subject}_{task}_{timestamp}`, the same as the session files.
- **Video:** 640×480 at 30 FPS by default (`CAM_BOX_RESOLUTION` and `CAM_BOX_FRAMERATE`
  in `SETTINGS` → `CAMERA SETTINGS`).

The box camera records from the start to the end of every session with a subject. If
the camera has to be restarted during the session, the pieces are merged back into one
video when the session ends.

| Column | Description |
| :--- | :--- |
| `frame` | Frame index. |
| `trial` | Trial running during that frame. |
| `annotation` | Text set from the task with `cam_box.write_text()` (empty if none). |
| `timestamp` | Capture time of the frame (Unix timestamp, Raspberry Pi clock). |
| `x_position` | X coordinate of the animal's center of mass. Only with `CAM_BOX_TRACKING_POSITION` ON. |
| `y_position` | Y coordinate of the animal's center of mass. Only with `CAM_BOX_TRACKING_POSITION` ON. |

#### Corridor Videos (continuous)

- **Storage path:** `data/videos/`
- **Filename format:** `CORRIDOR_{timestamp}`
- **Video:** 640×480 at 10 FPS by default (`CAM_CORRIDOR_FRAMERATE` in `SETTINGS` →
  `CAMERA SETTINGS`; the resolution is fixed).

The corridor camera records 24/7, starting a new file every `CORRIDOR_VIDEO_DURATION`
seconds (30 minutes by default). These videos are not synchronized and are deleted after
`DAYS_OF_VIDEO_STORAGE` days (see [Data Persistence & Backups](../preparation/backup.md)).

| Column | Description |
| :--- | :--- |
| `frame` | Frame index. |
| `annotation` | The most recent system event (the same text shown on the video). |
| `timestamp` | Capture time of the frame (Unix timestamp, Raspberry Pi clock). |

### Frame Annotations & On-Screen Overlays

Both cameras render diagnostic text overlays burnt directly into the video frames.

**Operant box camera:**
- **Top row:** `<filename>  trial: N  <annotation text>` — filename, trial number, and
  optional custom text set from within the task.
- **Bottom row:** `<duration>  frame: N  area1: N  area2: N...` — elapsed recording time,
  frame number, and pixel counts for each active tracking area.

**Corridor camera:**
- **Top row:** `<filename>  <annotation text>` — filename and the timestamp and
  description of the most recent system event.
- **Bottom row:** `<duration>  frame: N  area1: N  area2: N...` — same format as above.

In addition to the text overlays, when `VIEW_DETECTION` is enabled the system draws two
additional visual layers: the thresholded detection mask, and the boundary lines
delimiting each active tracking area. This option is configurable under `MONITOR` →
`DETECTION SETTINGS`, but the corridor and box cameras handle it very differently:

- **Corridor:** `VIEW_DETECTION_CORRIDOR` is drawn with cv2 directly onto the frame, so
  it is burnt into the saved video file as well as the live preview.
- **Operant box:** `VIEW_DETECTION_BOX` is drawn with QPainter on top of the live
  preview widget only — it is **never** encoded into the saved video, regardless of
  whether it is enabled or disabled.

```{note}
In practice, both can be left permanently enabled, though for different reasons:

Keep `VIEW_DETECTION_CORRIDOR` permanently enabled. Corridor recordings are not
critical data, and having the overlay burnt in makes it easy to verify at a glance that
pixel detection is working correctly across all areas.

`VIEW_DETECTION_BOX`, on the other hand, never touches the saved video, so there is no
downside to leaving it permanently enabled too — it only adds a live visual aid on the
`MONITOR` screen while you work.
```

See the [Custom Camera Drawing][CAMERA] section for how this `draw` (disk + screen) vs.
`draw_preview` (screen only) split also applies to overlays you add yourself.

---

### How the Data Files Drive Automated Training

The Training Village uses a closed-loop parameter cycle to drive fully autonomous
training progression across days without requiring human intervention:

```text
              [ subjects.csv ]
         (Reads current next_settings)
                     │
                     ▼
        [ Active Behavioral Session ]
                     │
       (Saves parameters actually used)
                     ▼
  [ {filename}.json + sessions_summary.csv ]
                     │
       (Session ends → training_protocol.py
        evaluates performance history)
                     ▼
  [ Updated next_settings in subjects.csv ]
```

1. **Initialization:** When an animal is recognized, its profile variables are loaded
   from the `next_settings` field in `subjects.csv`.
2. **Archiving:** The parameters used for the current session are saved to
   `{filename}.json`, and also, as a JSON string, to the `settings` column of that
   session's row in `sessions_summary.csv`.
3. **Evaluation:** At the end of the session, `training_protocol.py` runs automatically
   and analyzes the animal's historical performance trends from `{subject}.csv`.
4. **Update:** The script computes the adjusted parameters for the next session
   (advancing stages, modifying task variables, or updating the refractory period) and
   writes them back to the `next_settings` field in `subjects.csv`.



[CREATE]: /protocols/project_structure.md
[CAMERA]: /devices/camera.md
