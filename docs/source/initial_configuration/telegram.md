## Create a Telegram Bot
1. Install **Telegram** on your phone and open the app.

2. In the search bar, type **@BotFather** and select it.
   Be careful: there may be other bots with similar names. The official BotFather has a **blue verification checkmark**.

3. Send the command `/newbot`

4. Follow BotFather’s instructions to create your bot.
- At the end, you will receive a **token**.
- Write it down and **never share your token publicly** (e.g., on GitHub).

5. Open a chat with your new bot and activate it by sending `/start`




### Check the Token of an Existing Bot
1. Open the chat with **@BotFather**.

2. Send: `/token`

3. Select the bot whose token you want to retrieve.



### Configure the Bot to Trigger Alarms
1. Create a **group chat** that includes:
- The bot (make it **administrator**: *Group → Edit → Administrators*).
- Other participants who should receive the alarms.

→ Everyone in this group will receive alarms and can send commands to the bot.

2. To obtain the **group chat ID**:
- Start a conversation with **@username_to_id_bot** (IDBot).
- Forward any message from the group to IDBot.
- IDBot will reply with the **chat ID**-

3. Copy the values into your **Village settings** t(he settings are stored in a system file that never leaves your Raspberry Pi and is never shared with anything else.)
```ini
TELEGRAM_TOKEN = <your-bot-token>
TELEGRAM_CHAT  = <group-chat-id>
```

<br>
