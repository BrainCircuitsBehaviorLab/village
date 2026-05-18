## Remote Heartbeat Monitoring

Ensuring continuous system uptime and internet connectivity is a critical safety requirement for the Training Village ecosystem. In the event of a localized power outage, an animal could potentially become trapped inside the operant box without access to water. Because a dead system cannot broadcast native alarms, a local failure would otherwise go unnoticed until the system fails to deliver its automated twice-daily status reports (sent during the day/night cycle transitions).

To detect system failures immediately, the Training Village utilizes an external "dead man's switch" monitoring service called [healthchecks.io](https://healthchecks.io/).

Instead of the server reaching into your Raspberry Pi, the Training Village background service sends an outbound HTTP request (a "heartbeat" or "ping") to healthchecks.io every hour. If the service does not receive this ping within the expected timeframe, it concludes that your system has lost power or internet, and instantly alerts your team.

---

### Step-by-Step Setup Guide

#### Phase 1: Configure Healthchecks
1. Go to healthchecks.io and create a free account.
2. Once logged into your dashboard, click **Add Check**.
3. Configure the check's timing parameters:
   * **Period:** Set this to `1 hour`. This is how often your Raspberry Pi will check in.
   * **Grace Time:** Set this to `5 minutes`. This prevents false alarms caused by minor network lag or timing variations.
   * **Name:** Give it a recognizable name, such as `Training Village - Lab Room X`.
4. Look for the unique **Ping URL** generated for this check (it will look like `https://hc-ping.com/your-unique-uuid`). Copy this URL to your clipboard.

#### Phase 2: Link Healthchecks to Your Telegram Group
To ensure all connectivity alerts arrive in the exact same Telegram group chat used by your system bot:
1. On your healthchecks.io dashboard, click on the **Integrations** tab at the top.
2. Locate the **Telegram** option and click **Add Integration**.
3. Follow the on-screen instructions provided by the healthchecks bot. It will prompt you to invite the healthchecks notification bot into your existing laboratory group chat and provide the same **Group Chat ID** you retrieved during the Telegram setup phase.
4. Send a test notification from the dashboard to verify that the group chat receives the alert successfully.

#### Phase 3: Update Your Village Settings
1. Open a terminal on your Raspberry Pi and launch the application interface by typing `village`.
2. Navigate to **SETTINGS** → **TELEGRAM SETTINGS**.
3. Locate the **HEALTHCHECKS_URL** field and paste your unique Ping URL there.
4. Save your changes and exit.

```{admonition} Uptime Verification
:class: tip
Once saved, the Training Village will immediately send its first heartbeat signal. Refresh your healthchecks.io dashboard web page; the status indicator for your check should turn from a grey "New" state into a green "Passed" state.
```

<br>
