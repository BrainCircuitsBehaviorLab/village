## System State Machine

![State machine](/_static/states.png)

This is the state diagram of all possible system states and their descriptions.

Black arrows represent events that trigger a state transition, while red arrows indicate possible alarms, which may or may not cause a state change.

States in green represent a normal cycle in automatic mode. States in blue indicate manual manipulation of the system by a user. The orange state is reached after an error that the system cannot resolve on its own, requiring remote intervention.

Lighter-colored states are transitional and resolve quickly, leading to darker-colored states, which are stable states.

### Normal Cycle for an Animal Session

A typical session of an animal performing a task follows this sequence:

1. `WAIT`: The system remains in this state until an RFID detection occurs.
2. `DETECTION`: In this state, the system determines whether the subject is allowed to enter the behavioral box.
3. `ACCESS`: If the subject is allowed to enter, Door 1 is closed, and Door 2 is opened.
4. `LAUNCH_AUTO`: The task is automatically launched.
5. `RUN_FIRST`: The task begins, but Door 2 remains open until the corridor is empty.
6. `CLOSE_DOOR2`: Once the corridor is empty, Door 2 is closed.
7. `RUN_CLOSED`: The task is running, and the subject inside the behavioral box is not allowed to leave until a configurable minimum time for the task has elapsed.
8. `OPEN_DOOR2`: Once the minimum time has elapsed, Door 2 opens.
9. `RUN_OPENED`: The subject is allowed to leave the behavioral box if desired, or it may continue performing the task. At this point, two possible scenarios can occur:

#### Option A: The Subject Leaves Before the Task’s Maximum Time

If the scale detects that the animal is returning to the home cage, the system transitions to:

9. `EXIT_UNSAVED`: Door 2 is closed, and Door 1 is opened to allow the subject to return home.
10. `SAVE_OUTSIDE`: After the subject has returned to the home cage, the task is closed, and all data is saved.


#### Option B: The Subject Stays in the Box Until the Maximum Time

If the subject does not leave the behavioral box before the task’s maximum time is reached, the system transitions to:

9. `SAVE_INSIDE`: The task is closed, and all data is saved while the subject is still inside the behavioral box.
10. `WAIT_EXIT`: Until the subject attempts to leave and is detected by the scale.
11. `EXIT_SAVE`: Once detected by the scale, Door 2 is closed, and Door 1 is opened, allowing the subject to return to the home cage.

#### In Both Cases

The system transitions back to the initial WAIT state, ready for the next session.
