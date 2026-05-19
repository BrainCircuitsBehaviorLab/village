## Subject Management

To create a new subject, some data is required: a unique name, the tag ID of its RFID capsule, and its baseline weight. To obtain the RFID tag, place the animal in the corridor area where the RFID reader is located. Go to the `MONITOR` screen and ensure the `RFID reader` is activated. The animal should be detected, and its tag will appear in a log message at the bottom of the screen. To view this message, make sure `INFO` is selected so that the log appears at the bottom.

```{note}
All messages displayed in `INFO` are recorded in the `/data/events.csv` file located in your project folder. You can also preview this CSV file by going to the `DATA` screen and checking the `EVENTS` table.
```

Next, go to the `DATA` screen and select the `SUBJECTS` table. By clicking the `ADD` button, a new row representing a subject will be created. Complete or edit its parameters as follows:
- `name`: The subject’s name.
- `tag`: The ID of its RFID capsule.
- `basal_weight`: Weigh the animal to record its baseline weight as a reference.
- `active`: Controls when the subject is allowed to access the behavioral box. The available options are:
  - **ON**: the subject can access the box at any time.
  - **OFF**: the subject cannot access the box.
  - **Custom schedule**: by double-clicking the cell, a dialog opens where you can select specific days of the week and, for each day, the individual hours (0–23) during which the subject is active. This allows fine-grained control — for example, restricting access to weekdays between 8:00 and 20:00.
- `next_session_time`: By default, this is set to the date and time the subject is created. After each session ends, the training protocol automatically updates this field to schedule the next allowed session.
- `next_settings`: Stores the task variables that will be applied at the start of the subject’s next session. When a subject is created, these values are automatically populated with the default values defined in the training protocol. To inspect or modify them, double-click the cell to open an editor showing all available variables. After each session ends, the training protocol automatically updates this field based on the subject’s performance and the progression logic you have defined.

```{note}
If new variables are added to the training protocol after a subject has already been created, they will appear automatically with their default values the next time the `next_settings` cell is opened or the table is saved — no manual update is required. Variables that are removed from the protocol will silently disappear on the next save.
```

```{warning}
Renaming a variable in the training protocol is strongly discouraged once data collection has started. The system identifies variables by name, so renaming one causes its stored value to be permanently lost for all existing subjects — the renamed variable will revert to its default value on the next session.
```

<br><br><br>
