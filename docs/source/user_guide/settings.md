## Initial Settings

Some initial settings must be configured before the system can be used. Go to the `SETTINGS` screen and adjust the following parameters:

- `MAIN SETTINGS`: For animals on a day/night cycle with changing room lighting, set `DAYTIME` and  `NIGHTTIME` to ensure camera detection thresholds automatically switch between day and night modes. Adjust the `DETECTION COLOR` parameter if light-colored animals are being used on a dark corridor.

- `SOUND SETTINGS`:  If using sounds, enable `USE_SOUNDCARD` and select the **RPi DAC Pro** device from the `SOUND_DEVICE` list.

- `SCREEN SETTINGS`: If a screen or touchscreen is used to present stimuli, select the type in `USE_SCREEN` and configure the remaining parameters.

- `BPOD SETTINGS`: Set up the ports to be used (BNC, and BEHAVIOR ports).

- `TELEGRAM SETTINGS`: If a Telegram bot is already configured, enter the obtained token in `TELEGRAM_TOKEN`, the chat ID for notifications in `TELEGRAM_CHAT`, and the IDs of users authorized to access the bot in `TELEGRAM_USERS`.

```{important}
Never share the TELEGRAM_TOKEN. Settings are stored in a private .INI file outside of the repository folder to prevent accidental sharing on GitHub or similar platforms.
```
