## Custom Telegram Commands

```{admonition} Note
:class: note
The Telegram bot must be enabled and configured before custom commands can be
used. See [Telegram Bot Integration](../preparation/telegram.md) for setup.
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


class EchoCommand(TelegramCommandBase):
    """Custom command: /echo <text> — replies with the same text."""

    command = "echo"
    description = "Replies with the same text, e.g. /echo hello"

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # The words written after the command arrive in context.args, as strings.
        if not context.args:
            await update.message.reply_text("Usage: /echo <text>")
            return
        await update.message.reply_text(" ".join(context.args))
```

A complete example with two commands, one of them reading an argument:
[telegram_commands.py](../examples/telegram_commands.md).

```{toctree}
:hidden:

Custom Telegram Example <../examples/telegram_commands.md>
```
