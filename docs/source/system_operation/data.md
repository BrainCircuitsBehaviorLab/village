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
├── bpod_water_calibration.csv
├── sound_calibration.csv
├── temperatures.csv
└── deleted_sessions.csv
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
  :class: tip
  For the `water` column to be populated, water intake must be explicitly recorded within
  the task definition (see [PROTOCOL & TASK DESIGN][CREATE]).
  ```

#### Other Data Files

- **`temperatures.csv`**: Hourly temperature and humidity log, recorded automatically.
  Columns: `date`, `temperature`, `humidity`.

- **`calibration_files.csv`**: Registry of saved calibration files. Different calibration
  types can be created and customized (e.g. `sound_calibration`, `camera_calibration`,
  `bpod_water_calibration`), and their stored values can be retrieved and used within
  tasks.

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

### Video Recordings & Frame Data

- **Storage path:** `data/videos/{subject}/`
- **Filename format:** `{subject}_{task}_{timestamp}`

Each recording session produces two files:

- **`{filename}.mp4`**: H.264-encoded video. Default resolution is 640×480 at 30 FPS
  (configurable via system settings).
- **`{filename}.csv`**: Per-frame data table:

| Column | Description |
| :--- | :--- |
| `frame` | Frame index. |
| `trial` | Active trial number during that frame. |
| `annotation` | Custom text string pushed dynamically from the running protocol. |
| `timestamp` | Absolute hardware sensor capture time. |
| `x_position` | Center-of-mass X coordinate of the animal *(tracking must be enabled)*. |
| `y_position` | Center-of-mass Y coordinate of the animal *(tracking must be enabled)*. |

### Frame Annotations & On-Screen Overlays

Both cameras render diagnostic text overlays burnt directly into the video frames.

**Operant box camera:**
- **Top row:** `<filename>  trial: N  <annotation text>` — filename, trial number, and
  optional custom text set from within the task.
- **Bottom row:** `<duration>  frame: N  area1: N  area2: N...` — elapsed recording time,
  frame number, and pixel counts for each active tracking area.

**Corridor camera:**
- **Top row:** `<filename>  <annotation text>` — filename and the timestamp and
  description of the most recent system event (no trial number, as the corridor is not
  trial-structured).
- **Bottom row:** `<duration>  frame: N  area1: N  area2: N...` — same format as above.

In addition to the text overlays, when `VIEW_DETECTION` is enabled the system burns two
additional visual layers directly into the saved video: the detection pixels highlighted
in black, and the boundary lines delimiting each active tracking area. This option is
configurable under `MONITOR` → `DETECTION SETTINGS`. For performance reasons, these
overlays are computed on the same stream used for the live display and the saved
recording.

```{tip}
We recommend keeping `VIEW_DETECTION_CORRIDOR` permanently enabled for the corridor
camera. Corridor recordings are not critical data, but having the overlay active makes it
easy to verify at a glance that pixel detection is working correctly across all areas.

For the operant box, we recommend keeping `VIEW_DETECTION_BOX` disabled during normal
operation so that task videos are saved clean. Because the
operant box is typically a closed, controlled environment, illumination conditions are
stable and threshold recalibration is rarely needed. When it is required, simply enable
`VIEW_DETECTION_BOX`, adjust the thresholds, and disable it again.
```

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

Created in real time, one row per event:

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

A parsed, trial-by-trial overview generated at the end of each trial by processing the
raw data. Instead of one row per event, this file contains one row per trial. It begins
with the following fixed columns: `session`, `date`, `trial`, `subject`, `task`,
`system_name`, `run_mode`.

```{admonition} run_mode
The `run_mode` field is set to `manual` if the session was launched manually from the
GUI, or `auto` if it was triggered automatically upon detecting an animal in the corridor.
```

#### 3. Session Settings Metadata (`{filename}.json`)

Stores all parameters used during the session: `minimum_duration`, `maximum_duration`,
`run_mode`, `observations`, and all custom protocol parameters.

To add a note to a session, click on its entry in `sessions_summary` within the GUI. A
panel listing all session parameters will appear; the `observations` field is editable
and empty by default.

```{admonition} Tip
:class: tip
Although `.json` files already capture all parameters used in a session, it is good
practice to also record relevant variables from within the task using `register_value()`,
as this makes them directly accessible in the `.csv` file.
```

#### Aggregate History File

In addition to the per-session files, a persistent history file is maintained in each
subject's directory:

- **`{subject}.csv`**: Compiles every historical session completed by that animal. New session rows are appended each time a session ends. This aggregate dataset is essential for adaptive automated training (`training_protocol.py`), allowing the system to evaluate progression milestones — for example, verifying whether an animal achieved >80% accuracy over its last three sessions before advancing to the next training stage.

---

### Understanding the Automated Training Loop

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
             [ {filename}.json ]
                     │
       (Session ends → training_protocol.py
        evaluates performance history)
                     ▼
  [ Updated next_settings in subjects.csv ]
```

1. **Initialization:** When an animal is recognized, its profile variables are loaded
   from the `next_settings` field in `subjects.csv`.
2. **Archiving:** The parameters used for the current session are saved to
   `{filename}.json`.
3. **Evaluation:** At the end of the session, `training_protocol.py` runs automatically
   and analyzes the animal's historical performance trends from `{subject}.csv`.
4. **Update:** The script computes the adjusted parameters for the next session
   (advancing stages, modifying task variables, or updating the refractory period) and
   writes them back to the `next_settings` field in `subjects.csv`.



[CREATE]: /protocols/creating.md
