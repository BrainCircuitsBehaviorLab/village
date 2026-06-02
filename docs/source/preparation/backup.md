## Data Persistence & Backups

For safety and storage reasons, all behavioral data (session data and videos) should be
synchronized to a remote server or external hard drive.

Because the system runs on a microSD card with a limited capacity of 256 GB, older video
files must be regularly purged to make room for new recordings. Note that **behavioral
task data is never deleted from the microSD card** — only video files are removed.

By default, the system retains one week of video storage, but this window can be adjusted
under `SETTINGS` → `ADVANCED SETTINGS` → `DAYS_OF_VIDEO_STORAGE`.

At the end of each behavioral session, the system automatically triggers a data
synchronization routine. To specify your backup destination, configure the fields under
`SETTINGS` → `SYNC SETTINGS`, where you can choose between syncing to a remote network
server or to an external hard drive connected directly to the Raspberry Pi.

```{admonition} Warning
Corridor videos, which are recorded continuously 24/7, are **not** synchronized to any
backup destination and are automatically deleted after one week — the same retention
policy that applies to task videos. This is intentional, as continuous recordings would
otherwise consume an impractical amount of storage space.
```

### Key Configuration Fields

Two parameters govern the backup and deletion behavior:

- **`SAFE_DELETE`**
  - **`ON`:** Video files are only deleted after the system confirms they have been
    successfully backed up to the remote server or external hard drive.
  - **`OFF`:** Video files are automatically purged once they exceed the retention window,
    regardless of whether a backup exists.

- **`MAXIMUM_SYNC_TIME`:** Maximum duration (in seconds) allowed for a synchronization
  session to complete. If the process exceeds this threshold, it is terminated
  automatically. This prevents a slow network connection or a stalled transfer from
  blocking other animals from accessing the operant box.

```{admonition} Note
:class: tip
When synchronizing to a remote server, the `SERVER_PORT` field can be left blank if no
specific port needs to be defined for the SSH connection.
```
