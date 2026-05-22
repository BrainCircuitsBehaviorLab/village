
### Launching the TV Application

The Training Village is now ready to start. To launch the software, open a terminal window (press `Ctrl + Alt + T` or click the terminal icon in the taskbar next to the Raspberry Pi logo) and type:

```
village
```

This command activates a Python environment (.env) and runs the file `/home/pi/village/village/main.py` which will start the program and display the GUI.

#### Automatic Component Check

When the GUI launches, the system immediately performs an automated self-diagnostic check on all essential hardware connections (such as cameras, temperature sensors, scales, etc.). If a connection to a critical component cannot be established, a warning message will appear, and the Training Village will enter Debug Mode.

```{admonition} Note:
:class: tip
Upon your very first boot, you will likely receive warnings stating that telegram_bot and box_chip are not functioning. This is perfectly normal if you have not configured Telegram yet or if you haven't connected the physical Box Board satallite module. You can safely ignore these specific warnings for now; they will not prevent the core system from running.
```

#### Navigation and Camera Feeds

Once the GUI is active, a navigation menu will appear at the top of the window featuring the following tabs: `MAIN`, `MONITOR`, `SUBJECTS`, `TASKS`, `DATA`, `CALIBRATION`and `SETTINGS`.

To verify your live video streams:

Navigate to the `MONITOR` section.

Check that both camera streams are rendering properly. By default, the corridor camera should appear on the left side of the screen, and the operant box camera should appear on the right.

If the video feeds are inverted (i.e., the operant box camera is displaying on the left), you can quickly correct this in the software:

Navigate to `SETTINGS → CAMERA SETTINGS`.

Swap the camera index numbers (toggle 0 and 1 between the feeds) so they map correctly to your physical setup.
