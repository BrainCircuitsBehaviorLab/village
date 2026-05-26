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

```{admonition} Behind the Scenes:
:class: tip
When you run the village command, the system automatically executes a shortcut script that handles the background environment setup. Specifically, it activates your Python virtual environment by running source `~/.env/bin/activate` and then executes the core script located at `/home/pi/village/village/main.py` to start the program and display the GUI.
```


### Automatic Component Check

When the GUI launches, the system immediately performs an automated self-diagnostic check on all essential hardware connections (such as cameras, temperature sensors, scales, etc.). If a connection to a critical component cannot be established, a warning message will appear, and the Training Village will enter Debug Mode.

```{admonition} Note:
:class: tip
Upon your very first boot, you will likely receive warnings stating that telegram_bot and box_chip are not functioning. This is perfectly normal if you have not configured Telegram yet or if you haven't connected the physical Box Board satallite module. You can safely ignore these specific warnings for now; they will not prevent the core system from running.
```
