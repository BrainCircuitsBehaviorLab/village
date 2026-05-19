## Telegram Bot Integration

### Simple Overview
Integrating Telegram into the Training Village (TV) system allows you to receive automated, real-time safety alarms and query the live status of your system directly from your mobile phone.

To set this up, we will perform three simple phases:
1. Create a dedicated Telegram bot using the official account (**@BotFather**) to obtain an access token.
2. Set up a laboratory group chat containing the team and the bot, then use an identification bot to retrieve the unique **Group Chat ID**.
3. Save these credentials locally inside your Training Village configuration file on the Raspberry Pi.

---


### Detailed Step-by-Step Guide

#### Step 1: Create a New Telegram Bot
1. Open the **Telegram** app on your phone or computer.
2. In the search bar, type **@BotFather** and select it.

```{important}
Ensure you choose the official account featuring the **blue verification checkmark** to avoid fake clone bots.
```
3. Send the command `/newbot`.
4. Follow the step-by-step prompts provided by BotFather to assign a display name and a unique username for your bot.
5. Once complete, BotFather will generate an API **Token**. Copy this token immediately and store it safely. **Never share this token publicly** (e.g., do not commit it to public GitHub repositories).
6. Click the link to your new bot provided by BotFather, open a direct chat with it, and click **Start** (or send `/start`) to activate it.

```{hint}
If you ever need to retrieve the token of an existing bot, simply open your chat with **@BotFather**, send `/token`, and select your target bot from the menu.
```

#### Step 2: Configure the Alarm Group Chat
1. Create a new **Group Chat** in Telegram.
2. Add all laboratory members who need to receive system alarms, and add your newly created **bot** to the group.
3. Promote the bot to an **Administrator**: Navigate to *Group Info → Edit → Administrators → Add Administrator* and select your bot. This grants it the necessary permissions to transmit alarms to the group.
```{admonition} Result
:class: important
Anyone added to this group will receive automated alarms and can send text commands to control or query the bot.
```

#### Step 3: Retrieve the Group Chat ID
1. Search for **@username_to_id_bot** (commonly known as IDBot) in Telegram and start a chat with it.
2. Go back to your newly created lab group chat, send a temporary message, and **forward** that message directly into your chat with IDBot.
3. IDBot will immediately reply with your unique **Group Chat ID** (typically a long negative number, e.g., `-100xxxxxxxxx`). Copy this number exactly, including the minus sign if present.


#### Step 4: Update Your Village Settings

1. Open a terminal on your Raspberry Pi and launch the application interface by typing `village`.
2. Within the Training Village menu, navigate to **SETTINGS** and select the **TELEGRAM SETTINGS** subsection. Update the fields with your newly acquired credentials:

TELEGRAM_TOKEN

TELEGRAM_CHAT

```{admonition} Security Note
:class: warning
These configuration settings are saved strictly on your local Raspberry Pi storage. Your credentials never leave your hardware and are never uploaded or shared externally.
```


---


### Managing Alarms & Commands
Once your bot is fully linked to the system, you can refer to the [Alarm system overview][ALARM] section of the documentation. There you will find a complete reference list of interactive commands you can text to the bot to check system health, alongside a detailed breakdown of the automated alarm types the Training Village can trigger.

To verify that everything is working correctly, go to your Telegram group chat and send one of the following commands (ensuring the TV system is powered on and running). You should receive an immediate response from the bot:
- `/cam`
- `/report`
- `/plot`

<br><br><br>

[ALARM]: /troubleshooting/alarm.md
