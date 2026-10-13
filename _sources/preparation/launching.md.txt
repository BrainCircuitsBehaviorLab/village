## Launching the TV Application

Before launching the software for the first time, it is highly recommended to update your repository to ensure you are running the latest stable version. Open a terminal window (press `Ctrl + Alt + T` or click the terminal icon in the taskbar next to the Raspberry Pi logo), navigate to the project directory, and pull the latest changes from GitHub by running:

```
cd village
git pull
```

Once the repository is up to date, you can launch the software by typing:
```
village
```

```{admonition} Behind the Scenes
:class: note
`village` is a shortcut (an alias defined in `~/.bashrc`) that runs the core script
`/home/pi/village/village/main.py` with the Python of the virtual environment
(`/home/pi/.env/bin/python`), which starts the program and displays the GUI.
```

---

### Default Project
The first time the Training Village (TV) is launched, a default project named `demo-village-project` is created with several example tasks, copied from the Village installation into `~/village_projects/demo-village-project/code`. They are the same example files shown in [Protocol & Task Design](../protocol_index.rst), [Plotting](../plotting_index.rst) and [Advanced Customization](../advanced_customization_index.rst).

---

### Automatic Component Check

When the GUI launches, the system immediately performs an automated self-diagnostic check on all essential hardware connections (such as cameras, temperature sensors, scales, etc.). If a connection to a critical component cannot be established, a warning message will appear ("System running in debug mode").

```{admonition} Note
:class: note
Upon your very first boot, you will likely receive warnings stating that telegram_bot and box_chip are not functioning. This is perfectly normal if you have not configured Telegram yet or if you haven't connected the physical Box Board satellite module. You can safely ignore these specific warnings for now; they will not prevent the core system from running.
```
