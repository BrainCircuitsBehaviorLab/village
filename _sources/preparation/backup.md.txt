## Data Persistence & Backups

The Raspberry Pi stores everything on a 256 GB microSD card, so the data must be copied
regularly to a remote server or to an external hard drive, and old videos must be
deleted from the card to make room for new recordings. This is done automatically by
the system, at the end of each behavioral session, the system automatically synchronizes the data
with the selected backup destination. Old videos are deleted on every day/night change.

### What Is Synchronized

The project's `data/` folder (see [Saved Data and Video](../system_operation/data.md)):

- **Session data**: the raw and processed files of every session, their settings, and
  the history file of each subject.
- **Task videos**: the operant box videos and their per-frame data files.
- **System data**: events, subjects, sessions summary, temperatures, calibrations...

Not synchronized:

- **Corridor videos** (`CORRIDOR_*`), recorded continuously 24/7: copying them would
  take an impractical amount of storage space.

### What Is Deleted from the microSD Card

**Session data and system data are never deleted** from the card: only videos are.

- **Task videos** older than `DAYS_OF_VIDEO_STORAGE` days (7 by default,
  `SETTINGS` → `ADVANCED SETTINGS`) are deleted. With `SAFE_DELETE` ON (the default),
  only once the system has checked that they are already in the backup destination.
- **Corridor videos** older than `DAYS_OF_VIDEO_STORAGE` days are always deleted, since
  they are never synchronized.

```{warning}
Videos are only deleted when synchronization is enabled (`SYNC_TYPE` set to `HD` or
`SERVER`). With `SYNC_TYPE` set to `OFF`, no video is ever deleted, not even the corridor
ones, and the card will eventually fill up (the "Low disk space" alarm warns about it).
```

### Key Configuration Fields

These fields are found in `SETTINGS` → `SYNC SETTINGS`:

- **`SYNC_TYPE`:** where to sync the data.
  - **`HD`:** to an external hard drive connected to the Raspberry Pi.
  - **`SERVER`:** to a remote server, over SSH (see below).
  - **`OFF`:** no synchronization (not recommended).

- **`SYNC_DESTINATION`:** the base path of the backup: the path where the hard drive is
  mounted (e.g. `/media/pi/my_disk`), or a path on the server. The data are copied
  into `SYNC_DIRECTORY`, which is created automatically inside it with the project name
  followed by `_data` (in this example, `/media/pi/my_disk/demo-village-project_data`).

- **`SERVER_USER`, `SERVER_HOST`, `SERVER_PORT`:** only for `SERVER`: the user and
  hostname (or IP address) of the server, and the SSH port.

Two more parameters govern the backup and deletion behavior:

- **`SAFE_DELETE`**
  - **`ON`:** Task video files are only deleted after the system confirms they have been
    successfully backed up to the remote server or external hard drive.
  - **`OFF`:** Task video files are deleted once they exceed the retention window,
    regardless of whether a backup exists.

- **`MAXIMUM_SYNC_TIME`:** Maximum duration (in seconds, 1200 by default) allowed for a
  synchronization session to complete. If the process exceeds this threshold, it is terminated
  automatically. This prevents a slow network connection or a stalled transfer from
  blocking other animals from accessing the operant box.

```{admonition} Note
:class: note
When synchronizing to a remote server, the `SERVER_PORT` field can be left blank if no
specific port needs to be defined for the SSH connection.
```

### Syncing to a Server: SSH Access Without a Password

The Raspberry Pi connects to the server over SSH with no one there to type a password,
so it must be able to log in without one. The usual way to do this is with an SSH key.
How to set it up depends on the server, so ask its administrator. Before enabling the
synchronization, check from a terminal on the Raspberry Pi that
`ssh <SERVER_USER>@<SERVER_HOST>` (with `-p <SERVER_PORT>` if you set a port) logs in
without asking for a password: if it asks for one, the synchronization will fail.
