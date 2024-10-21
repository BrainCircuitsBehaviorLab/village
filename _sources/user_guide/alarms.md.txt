# Alarms

## Interrogate the system

- `/status ‘hours’` → Summary of what happened in the behavioral box the last hours.
- `/cam` → Screenshot of the cameras’ recording.
- `/plot ‘days’` → Gui plots.
- `/report ‘hours days’` → status+cam+plot.

## Alarms
<!--
### ALARM: check weight and water

**Very frequent**

Triggered when a mouse weighs less than 50% of its basal weight or has drunk less than 400 µl in the last 24 hours, or less than 1000 µl in the last 48h.

- **Weight**: Check intersession if all animals have a drop; it might indicate a lack of water or food in the setup, or that the scale is not working well. If it's a single animal, weigh it manually, assess its health score, and check its last session's performance. It might be too lost in the training.
- **Water**: Used to be very important but with CA we can relax. Check if the animal has been drinking less than 600 µl during 2-3 consecutive days, and if so, supplement manually with 500-1000 µl.

### ALARM: mouse has been more than ‘x’ seconds in the box

**Very frequent**

Connect remotely. If the mouse is sleeping, play a buzzer sound or open and close the door. It will exit automatically. If it doesn’t exit after a long time (>5 hours), go in person to check what happens. If the room temperature is very high, they tend to sleep more inside. If so, email Sergi.

### ALARM: Mouse trapped in the corridor

**Frequent**

Usually occurs when 2 mice overlap in the door 2 zone, allowing the task to start. This usually resolves itself, but if not, open door 1 remotely. This alarm can also be triggered if a mouse escapes from the cage and walks on top of the corridor. If you suspect this, check corridor videos where the alarm was triggered.

### ALARM: 2 mice in box

**Frequent**

Check the inner camera remotely. Can you see two mice? If yes, make them exit, delete the session, and check why with videos. If no, check if cam areas are overlapping with the touchscreen (false alarm). Adjust the areas in the camera settings manually.

### ALARM: Animal on the floor

**Very frequent**

Some animals learn how to go down (e.g., A49), and once they learn, they do it often. It’s not harmful, just annoying because they lose a lot of time exploring something unrelated to the task.

- If it’s a regular explorer, just ignore it.
- If it’s a new animal, check why it’s on the floor and if it knows how to come back. If not, you will need to help it manually.

Sometimes this is a false alarm when the camera is moved and areas are misplaced. If so, correct it.

### ALARM: Few trials

**Very frequent in novel animals**

- For well-trained animals: If triggered, something might be wrong in the behavioral box (e.g., a photogate is misplaced, or the pump is not working). Go in person and test the task manually.
- For novel animals: If triggered after being for a long time (>5 days) in the same stage, it means they are very lost in the training. Move them to an easier stage manually.

### ALARM: last session ended

**Rare**

Check remotely what’s happening:

- **Correct functioning of the doors**: If not, go in person and fix it (e.g., dust, motor, or Arduino issues).
- **RFID detections**: If not in the last few hours, check if the button is on.
- **Scale detection**: Tag scale and get weight 4-5 times. It should weigh slightly different numbers. If always 0, it’s likely not working—go in person to check connections.
- **Camera problems**: If the camera is not working, reload academy. If still not working, try `cd /dev → ls` in terminal to check if you can see the camera. If not, reconnect or change its port.
- **Academy script**: Ensure the script is running. If an error occurs, check for wrong lines in subjects or events.
- **Animal movement**: If everything works but animals are not moving, check in person if corridor access is closed or if animals are sick or have escaped.

### ALARM: Overdetections in ‘Session’

**Rare**

Indicates an abnormal amount of photogate beam crosses. This can happen due to interference from the buzzer port or misaligned photogates.

- If Buzzer (Port 2), go in person, connect, and disconnect the device. If it happens many days with the same device, change it.
- If photogates: Check in person if they are correctly aligned. If not, align them. If still not working, change the photogates.

### ALARM: touchscreen not working for ‘Subject’

**Rare**

Usually occurs due to electronic failures. If sporadic, ignore it. If frequent, disconnect the touch device, turn off the PC, reconnect it, and turn it on.

### ALARM: last heartbeat

**Rare**

PC is off or has lost internet connection. Go in person and check what’s happening.

### ALARM: bpod communication error

**Rare**

Sometimes Bpod fails. Ignore it unless it becomes frequent.

## Errors not detected by the alarm system

- **Ecohab not detecting**: Stop Ecohab script, disconnect USB & power supply. Reconnect everything in the following order: 1) Power supply 2) USB 3) Ecohab script. Check that all antennas (1-6) are detected.
- **High temperatures in the room**: Ventilation system is very bad; many times temperatures rise above 24ºC. Email Sergi.
- **Reloading academy**: Stops Ecohab. Be sure to play Ecohab after.
- **Inside camera freeze/doesn’t work**: Reload academy. If still not working, check `cd /dev ls` to find the camera. If not, change the device.
- **Bpod stuck in a task**: Close academy, unplug and plug Bpod (it becomes blue), wait 1 minute, and play academy again.
- **Sound not working**: Check buzzer cables, Bpod power supply (only affects high-pitch sounds).
- **Water not delivered**: Check pump, valves, refill bottle, calibrate.
- **Touchscreen ghost detections**: Remove mask, clean IR frame.
- **Screen issues**: Check cables and display settings. -->

| **Alarm**                                      | **Frequency**         | **Description**                                                                                  | **Recommended Actions**                                                                                                                                                                                                                       |
|------------------------------------------------|-----------------------|--------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Check weight and water**                     | Very frequent         | Triggered when a mouse weighs less than 50% basal weight or has drunk less than the threshold.    | - For weight: Check for intersession issues, manually weigh, assess health score, and review performance.  - For water: If below 600 µl for 2-3 days, supplement with 500-1000 µl manually.                                              |
| **Mouse in box for ‘x’ seconds**               | Very frequent         | Mouse has been in the box for a long time.                                                        | Connect remotely, play buzzer, open/close door. If no response >5 hours, go in person. Check temperature.                                                                                                                                   |
| **Mouse trapped in corridor**                  | Frequent              | Two mice overlap in the doors' zone, allowing task to start, or mouse escaped to corridor.        | Open door 1 remotely. If suspected escape, check corridor videos.                                                                                                                                                                           |
| **2 mice in box**                              | Frequent              | System detects two mice inside the box.                                                           | Verify via inner camera. If true, make them exit, delete session, and review videos. If false, check camera settings for overlap.                                                                                                             |
| **Animal on the floor**                        | Very frequent         | Mouse has learned to go down to the floor of the box.                                             | If a regular explorer, ignore. If a new animal, check if it knows how to return. Manually help if needed.                                                                                                                                   |
| **Few trials**                                 | Very frequent         | Indicates fewer trials than expected, common in new or poorly trained mice.                       | - Well-trained mice: Check the behavioral box and task manually.  - New mice: Consider moving to an easier stage if not improving.                                                                                                       |
| **Last session ended**                         | Rare                  | Session ended unexpectedly.                                                                       | - Check doors, RFID, and scale for issues.  - Ensure camera and script are running.  - Verify animal movement and room status.                                                                                                       |
| **Overdetections in ‘Session’**                | Rare                  | Abnormal number of photogate beam crosses detected.                                               | Check buzzer or photogate alignment. Adjust or replace components as needed.                                                                                                                                                                 |
| **Touchscreen not working for ‘Subject’**      | Rare                  | Touchscreen failure during session.                                                               | Disconnect and reconnect the device. Restart PC if the issue persists.                                                                                                                                                                      |
| **Last heartbeat**                             | Rare                  | PC is off or has lost internet connection.                                                        | Go in person to check for power or network issues.                                                                                                                                                                                           |
| **Bpod communication error**                   | Rare                  | Communication error between the Bpod and the system.                                              | Usually can be ignored unless it becomes frequent.                                                                                                                                                                                           |
| **Bpod not sending softcodes**                 | Never happens         | Issue with Bpod softcode transmission.                                                            | Ignore unless it starts happening frequently.                                                                                                                                                                                               |
| **Bpod not sending serials**                   | Never happens         | Issue with Bpod serial transmission.                                                              | Ignore unless it starts happening frequently.                                                                                                                                                                                               |
| **Ecohab not detecting**                       | Not detected by alarm | Antennas not detected by Ecohab.                                                                  | Restart Ecohab script, reconnect USB and power supply. Check antenna status.                                                                                                                                                                 |
