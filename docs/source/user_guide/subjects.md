## Create New Subjects

To create a new subject, some data is required: a unique name, the tag ID of its RFID capsule, and its baseline weight. To obtain the RFID tag, place the animal in the corridor area where the RFID reader is located. Go to the `MONITOR` screen and ensure the `Tag reader` is activated. The animal should be detected, and its tag will appear in a log message at the bottom of the screen. To view this message, make sure `SYSTEM_INFO` is selected so that the log appears at the bottom.

```{note}
All messages displayed in `SYSTEM_INFO` are recorded in the `/data/events.csv` file located in your project folder. You can also preview this CSV file by going to the `DATA` screen and checking the `EVENTS` table.
```

Next, go to the `DATA` screen and select the `SUBJECTS` table. By clicking the `ADD` button, a new row representing a subject will be created. Complete or edit its parameters as follows:
- `name`: The subject’s name.
- `tag`: The ID of its RFID capsule.
- `basal_weight`: Weigh the animal to record its baseline weight as a reference.
- `active`: Change the value to ON to allow the animal to access the behavioral box.
- `next_session_time`: By default, this is set to the date and time the subject is created.
- `next_settings`: Assigns the settings defined as default settings in the training protocol.
