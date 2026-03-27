# Trial Data Format

If you are **not** using the `pybpodapi` library, you must implement a method that returns trial data as a dictionary with the **exact** structure described below. This dictionary must be returned at the end of each trial.

## Required Dictionary Structure

```python
{
    "Trial start timestamp": float,
    "States timestamps": dict,
    "Events timestamps": dict,
}
```

## Field Descriptions

### `"Trial start timestamp"` → `float`

The time at which the trial started, expressed as a **UNIX epoch timestamp in seconds** (i.e., seconds since 1970-01-01 00:00:00 UTC).

You can obtain this value using:

```python
from datetime import datetime
trial_start_timestamp = datetime.now().timestamp()
```

### `"States timestamps"` → `dict[str, list[tuple[float, float]]]`

A dictionary where:
- Each **key** is the name of a state (`str`).
- Each **value** is a list of tuples `(start_timestamp, end_timestamp)`, representing every time that state was visited during the trial.
- Timestamps must be **absolute UNIX epoch timestamps in seconds**.
- If a state was defined but **never visited**, its value must be `[(float('nan'), float('nan'))]`.

Example:

```python
{
    "WaitForPoke": [(1711446000.000, 1711446001.234)],
    "Reward":      [(1711446001.234, 1711446002.567)],
    "ITI":         [(1711446002.567, 1711446003.000)],
    "Punish":      [(float('nan'), float('nan'))],  # not visited
}
```

### `"Events timestamps"` → `dict[str, list[float]]`

A dictionary where:
- Each **key** is the name of an event (`str`).
- Each **value** is a list of `float` timestamps (absolute UNIX epoch in seconds), one for each occurrence of that event during the trial.
- Only events that actually occurred should be included.

Example:

```python
{
    "Tup":      [1711446001.234, 1711446002.567],
    "Port1In":  [1711446000.500],
    "Port1Out": [1711446000.800, 1711446001.100],
}
```

## Complete Example

```python
from datetime import datetime

def get_trial_data() -> dict:
    return {
        "Trial start timestamp": 1711446000.000,
        "States timestamps": {
            "WaitForPoke": [(1711446000.000, 1711446001.234)],
            "Reward":      [(1711446001.234, 1711446002.567)],
            "ITI":         [(1711446002.567, 1711446003.000)],
            "Punish":      [(float('nan'), float('nan'))],
        },
        "Events timestamps": {
            "Tup":      [1711446001.234, 1711446002.567],
            "Port1In":  [1711446000.500],
            "Port1Out": [1711446000.800, 1711446001.100],
        },
    }
```

> [!IMPORTANT]
> - All timestamps must be in **seconds** (not milliseconds).
> - All timestamps must be **absolute** (UNIX epoch), not relative to the trial start.
> - State and event names are free-form strings, but should be consistent across trials.
