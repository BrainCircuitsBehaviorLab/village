## Custom Telegram Commands

```{admonition} Note
:class: note
The Telegram bot must be enabled and configured before custom commands can be
used. See [Telegram](../preparation/telegram.md) for setup.
```

You can add your own `/commands` to the Telegram bot by creating classes that
inherit from `TelegramCommandBase` in your project. Every matching class found
in your project is registered as a separate command, unlike most of the other
base classes, which only allow one inherited class each.

A custom command whose name collides with a built-in one (`start`, `help`,
`report`, `plot`, `cam`, `mice_checked`, `restart_anydesk`, `restart_vnc`) is
rejected and logged as an error instead of overriding it.

---

### Creating a custom Telegram command

Create a file (e.g. `telegram_commands.py`) in your `project/code` folder
containing one class per command, each inheriting from `TelegramCommandBase`.
Set `command` to the slash-command name (without the slash) and `description`
to a short one-line explanation shown by `/help`.

```python
from telegram import Update
from telegram.ext import ContextTypes

from village.custom_classes.telegram_command_base import TelegramCommandBase


class WaterCommand(TelegramCommandBase):
    """Custom command: /water <amount> — deliver a manual water reward."""

    command = "water"
    description = "Deliver a manual water reward, e.g. /water 10"

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            amount = float(context.args[0]) if context.args else 10.0
            # ... trigger the reward here ...
            await update.message.reply_text(f"Delivered {amount} µl of water.")
        except Exception:
            await update.message.reply_text("Usage: /water <amount>")
```
