## Create a Telegram Bot

1. Text `@BotFather` in the search tab and select this bot.
2. Text: `/newbot` and send.
3. Follow Botfather instructions. Write down the token. Never share the token in github.
4. Open a chat with your new bot and activate it by sending: `/start`.

### Check the token of an existing bot

5. Go to the `@BotFather` chat and send ``/token``.

### Make the bot triggers the alarms

6. Create a chat with the bot and other participants (the bot must be admin: go to the group → edit → administrators). All the participants of this group will receive the
alarms from the bot and will be able to send commands to it.
7. Start a conversation with `@username_to_id_bot` to obtain your ID, the chat ID and
the ID of all the other users.
8. Copy the token, the chat ID and the allowed users IDs in academy settings (TELEGRAM_TOKEN, TELEGRAM_CHAT, TELEGRAM USERS)
