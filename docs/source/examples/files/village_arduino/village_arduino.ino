// Firmware for all the Arduino examples.
//
// One sketch for the six arduino_* example tasks and for the water
// calibration (water_calibration_arduino.py), so the board does not need a
// different firmware for every task. Each task sends its own command; this
// sketch runs that trial by itself and reports back what happened, with its
// own timing.
//
// Protocol:
//   Pi -> Arduino: one message per trial (or per valve opening), starting
//   with a command byte that says which task it is for and how many bytes
//   follow (see messageSize()). The rest of each message is described above
//   the function that handles it.
//
//   Arduino -> Pi, 6 raw bytes per message:
//     [EVENT_POKE, port, elapsed_ms (uint32, little-endian)]
//       -- a poke on a port.
//     [EVENT_TRIAL_END, result, elapsed_ms (uint32, little-endian)]
//       -- once, when the trial is over (result depends on the task).
//     [EVENT_STATE, state, elapsed_ms (uint32, little-endian)]
//       -- every time the trial enters a new state, so the Pi can register
//          it with register_enter_state. State ids are per task: each
//          task's .py file translates its own (STATE_NAMES).
//     [EVENT_VALVE_CLOSED, port, elapsed_us (uint32, little-endian)]
//       -- water calibration only (see openValve()).
//   elapsed_ms is milliseconds since this sketch received the command for
//   the current trial (its own timer, reset every trial). It is the
//   controller clock: the Pi registers the trial start as controller time 0
//   at the moment it sent the command, and every elapsed_ms as a
//   controller timestamp, so the two clocks never need to be synchronized.
//
// 3 ports are wired: 1 (left), 2 (center), 3 (right); only the side ports
// (1 and 3) have a valve. Baud rate must match BAUDRATE in the .py files
// (9600).

// Commands (Pi -> Arduino), one per task
const byte CMD_HABITUATION = 11;        // arduino_1_habituation.py
const byte CMD_PASSIVE = 12;            // arduino_2_passive.py
const byte CMD_ACTIVE = 13;             // arduino_3_active.py
const byte CMD_CENTER_INITIATED = 14;   // arduino_4_center_initiated.py
const byte CMD_INTRODUCE_PENALTY = 15;  // arduino_5_introduce_penalty.py
const byte CMD_DELAY = 16;              // arduino_6_delay.py
const byte CMD_OPEN_VALVE = 20;         // water_calibration_arduino.py

// Events (Arduino -> Pi)
const byte EVENT_POKE = 1;
const byte EVENT_TRIAL_END = 2;
const byte EVENT_STATE = 3;
const byte EVENT_VALVE_CLOSED = 4;

const byte LEFT_PORT = 1;
const byte CENTER_PORT = 2;
const byte RIGHT_PORT = 3;

const byte pokePinLeft = 22;
const byte pokePinCenter = 24;
const byte pokePinRight = 26;
const byte valvePinLeft = 39;
const byte valvePinRight = 43;
const byte ledPinLeft = 23;
const byte ledPinCenter = 25;
const byte ledPinRight = 27;

// Edge state for each side poke pin, so a poke that's held down only
// reports once, and a second, separate poke on the same pin still gets
// reported (see readNewSidePoke()).
bool lastPokeLeft = false;
bool lastPokeRight = false;

void setup() {
  Serial.begin(9600);
  pinMode(pokePinLeft, INPUT);
  pinMode(pokePinCenter, INPUT);
  pinMode(pokePinRight, INPUT);
  pinMode(valvePinLeft, OUTPUT);
  pinMode(valvePinRight, OUTPUT);
  pinMode(ledPinLeft, OUTPUT);
  pinMode(ledPinCenter, OUTPUT);
  pinMode(ledPinRight, OUTPUT);
  digitalWrite(valvePinLeft, LOW);
  digitalWrite(valvePinRight, LOW);
  digitalWrite(ledPinLeft, LOW);
  digitalWrite(ledPinCenter, LOW);
  digitalWrite(ledPinRight, LOW);
}

// --- Messages ------------------------------------------------------------

// Total size of the message that starts with this command (command byte
// included), or 0 for an unknown command.
byte messageSize(byte command) {
  switch (command) {
    case CMD_HABITUATION: return 3;
    case CMD_PASSIVE: return 6;
    case CMD_ACTIVE: return 6;
    case CMD_CENTER_INITIATED: return 8;
    case CMD_INTRODUCE_PENALTY: return 8;
    case CMD_DELAY: return 10;
    case CMD_OPEN_VALVE: return 6;
    default: return 0;
  }
}

unsigned int readUInt16() {
  unsigned int value = (unsigned int)Serial.read();
  value |= ((unsigned int)Serial.read()) << 8;
  return value;
}

unsigned long readUInt32() {
  unsigned long value = 0;
  for (byte i = 0; i < 4; i++) {
    value |= ((unsigned long)Serial.read()) << (8 * i);
  }
  return value;
}

void sendEvent(byte eventCode, byte value, unsigned long elapsed) {
  Serial.write(eventCode);
  Serial.write(value);
  Serial.write((byte)(elapsed & 0xFF));
  Serial.write((byte)((elapsed >> 8) & 0xFF));
  Serial.write((byte)((elapsed >> 16) & 0xFF));
  Serial.write((byte)((elapsed >> 24) & 0xFF));
}

// --- Pokes ---------------------------------------------------------------

bool pokedCenter() {
  return digitalRead(pokePinCenter) == HIGH;
}

// Whichever side port is poked right now (level, not edge).
bool readSidePoke(byte &port) {
  if (digitalRead(pokePinLeft) == HIGH) {
    port = LEFT_PORT;
    return true;
  }
  if (digitalRead(pokePinRight) == HIGH) {
    port = RIGHT_PORT;
    return true;
  }
  return false;
}

// Rising-edge check on both side poke pins -- returns at most one
// newly-poked port per call, but is meant to be called every loop
// iteration so a poke on either pin is always eventually seen and reported
// exactly once per press (a second poke on the same pin, after it's gone
// low again, is reported again). Call resetSidePokes() before the loop.
bool readNewSidePoke(byte &port) {
  bool left = digitalRead(pokePinLeft) == HIGH;
  bool right = digitalRead(pokePinRight) == HIGH;
  bool result = false;
  if (left && !lastPokeLeft) {
    port = LEFT_PORT;
    result = true;
  } else if (right && !lastPokeRight) {
    port = RIGHT_PORT;
    result = true;
  }
  lastPokeLeft = left;
  lastPokeRight = right;
  return result;
}

void resetSidePokes() {
  lastPokeLeft = digitalRead(pokePinLeft) == HIGH;
  lastPokeRight = digitalRead(pokePinRight) == HIGH;
}

byte ledPinOf(byte port) {
  return (port == LEFT_PORT) ? ledPinLeft : ledPinRight;
}

byte valvePinOf(byte port) {
  return (port == LEFT_PORT) ? valvePinLeft : valvePinRight;
}

void deliverWater(byte port, unsigned int valveTimeMs) {
  byte valvePin = valvePinOf(port);
  digitalWrite(valvePin, HIGH);
  delay(valveTimeMs);
  digitalWrite(valvePin, LOW);
}

// --- Main loop -----------------------------------------------------------

// Reads the command byte first, waits until the whole message has arrived
// (its size depends on the command), and runs the trial it asks for.
void loop() {
  if (Serial.available() < 1) {
    return;
  }
  byte command = Serial.peek();
  byte size = messageSize(command);
  if (size == 0) {
    Serial.read();  // unknown command: drop it
    return;
  }
  if (Serial.available() < size) {
    return;  // the rest of the message has not arrived yet
  }
  Serial.read();  // the command byte

  switch (command) {
    case CMD_HABITUATION: {
      unsigned int durationS = readUInt16();
      runHabituation(durationS);
      break;
    }
    case CMD_PASSIVE: {
      byte port = Serial.read();
      unsigned int valveTimeMs = readUInt16();
      unsigned int ledOnTimeoutMs = readUInt16();
      runPassive(port, valveTimeMs, ledOnTimeoutMs);
      break;
    }
    case CMD_ACTIVE: {
      byte correctPort = Serial.read();
      unsigned int ledOnTimeoutMs = readUInt16();
      unsigned int valveTimeMs = readUInt16();
      runActive(correctPort, ledOnTimeoutMs, valveTimeMs);
      break;
    }
    case CMD_CENTER_INITIATED: {
      byte correctPort = Serial.read();
      unsigned int cLedOnTimeoutMs = readUInt16();
      unsigned int ledOnTimeoutMs = readUInt16();
      unsigned int valveTimeMs = readUInt16();
      runCenterInitiated(correctPort, cLedOnTimeoutMs, ledOnTimeoutMs, valveTimeMs);
      break;
    }
    case CMD_INTRODUCE_PENALTY: {
      byte correctPort = Serial.read();
      unsigned int cLedOnTimeoutMs = readUInt16();
      unsigned int ledOnTimeoutMs = readUInt16();
      unsigned int valveTimeMs = readUInt16();
      runIntroducePenalty(correctPort, cLedOnTimeoutMs, ledOnTimeoutMs, valveTimeMs);
      break;
    }
    case CMD_DELAY: {
      byte firstPort = Serial.read();
      unsigned int cLedOnTimeoutMs = readUInt16();
      unsigned int delayMs = readUInt16();
      unsigned int totalTimeoutMs = readUInt16();
      unsigned int valveTimeMs = readUInt16();
      runDelay(firstPort, cLedOnTimeoutMs, delayMs, totalTimeoutMs, valveTimeMs);
      break;
    }
    case CMD_OPEN_VALVE: {
      byte port = Serial.read();
      unsigned long timeUs = readUInt32();
      openValve(port, timeUs);
      break;
    }
  }
}

// === Habituation (arduino_1_habituation.py) ==============================
//
// [CMD_HABITUATION, duration_s (uint16, LE)]
// Watches the 3 ports for duration_s, ending the trial early the moment any
// one of them is poked. Reports [EVENT_TRIAL_END, port (0 if nobody
// poked)].

const byte HABITUATION_READY_TO_EXPLORE = 1;

byte readAnyPoke() {
  if (digitalRead(pokePinLeft) == HIGH) return LEFT_PORT;
  if (digitalRead(pokePinCenter) == HIGH) return CENTER_PORT;
  if (digitalRead(pokePinRight) == HIGH) return RIGHT_PORT;
  return 0;
}

void runHabituation(unsigned int durationS) {
  unsigned long t0 = millis();
  unsigned long durationMs = (unsigned long)durationS * 1000UL;
  sendEvent(EVENT_STATE, HABITUATION_READY_TO_EXPLORE, 0);

  byte pokedPort = 0;
  while (millis() - t0 < durationMs) {
    pokedPort = readAnyPoke();
    if (pokedPort != 0) {
      break;
    }
  }

  sendEvent(EVENT_TRIAL_END, pokedPort, millis() - t0);
}

// === Passive (arduino_2_passive.py) =======================================
//
// [CMD_PASSIVE, port, valve_time_ms (uint16, LE), led_on_timeout_ms (uint16, LE)]
// Delivers the reward up front, then keeps the LED on until that port is
// poked or the timeout runs out. A poke on the other port is reported but
// doesn't end the wait. Reports [EVENT_TRIAL_END, PASSIVE_GOT_CORRECT or
// PASSIVE_TIMEOUT].

const byte PASSIVE_WATER_DELIVERY = 1;
const byte PASSIVE_LED_ON = 2;
const byte PASSIVE_TIMEOUT = 0;
const byte PASSIVE_GOT_CORRECT = 1;

void runPassive(byte port, unsigned int valveTimeMs, unsigned int ledOnTimeoutMs) {
  unsigned long t0 = millis();
  byte ledPin = ledPinOf(port);

  sendEvent(EVENT_STATE, PASSIVE_WATER_DELIVERY, 0);
  digitalWrite(ledPin, HIGH);
  deliverWater(port, valveTimeMs);

  sendEvent(EVENT_STATE, PASSIVE_LED_ON, millis() - t0);
  resetSidePokes();
  bool gotCorrect = false;
  byte pokedPort = 0;
  unsigned long ledOnStart = millis();
  while (millis() - ledOnStart < ledOnTimeoutMs) {
    if (readNewSidePoke(pokedPort)) {
      sendEvent(EVENT_POKE, pokedPort, millis() - t0);
      if (pokedPort == port) {
        gotCorrect = true;
        break;
      }
    }
  }
  digitalWrite(ledPin, LOW);

  sendEvent(
    EVENT_TRIAL_END,
    gotCorrect ? PASSIVE_GOT_CORRECT : PASSIVE_TIMEOUT,
    millis() - t0
  );
}

// === Active (arduino_3_active.py) =========================================
//
// [CMD_ACTIVE, correct_port, led_on_timeout_ms (uint16, LE), valve_time_ms (uint16, LE)]
// Turns the LED of the correct port on and waits for a poke there; only
// then delivers the reward. A poke on the other port is reported but
// doesn't end the wait. Reports [EVENT_TRIAL_END, ACTIVE_GOT_CORRECT or
// ACTIVE_TIMEOUT].

const byte ACTIVE_LED_ON = 1;
const byte ACTIVE_WATER_DELIVERY = 2;
const byte ACTIVE_TIMEOUT = 0;
const byte ACTIVE_GOT_CORRECT = 1;

void runActive(byte correctPort, unsigned int ledOnTimeoutMs, unsigned int valveTimeMs) {
  unsigned long t0 = millis();
  byte correctLedPin = ledPinOf(correctPort);

  sendEvent(EVENT_STATE, ACTIVE_LED_ON, 0);
  digitalWrite(correctLedPin, HIGH);
  resetSidePokes();
  bool gotCorrect = false;
  byte pokedPort = 0;
  while (millis() - t0 < ledOnTimeoutMs) {
    if (readNewSidePoke(pokedPort)) {
      sendEvent(EVENT_POKE, pokedPort, millis() - t0);
      if (pokedPort == correctPort) {
        gotCorrect = true;
        break;
      }
    }
  }
  digitalWrite(correctLedPin, LOW);

  if (gotCorrect) {
    sendEvent(EVENT_STATE, ACTIVE_WATER_DELIVERY, millis() - t0);
    deliverWater(correctPort, valveTimeMs);
  }

  sendEvent(
    EVENT_TRIAL_END,
    gotCorrect ? ACTIVE_GOT_CORRECT : ACTIVE_TIMEOUT,
    millis() - t0
  );
}

// === Center initiated (arduino_4_center_initiated.py) =====================
//
// [CMD_CENTER_INITIATED, correct_port, c_led_on_timeout_ms (uint16, LE),
//  led_on_timeout_ms (uint16, LE), valve_time_ms (uint16, LE)]
// Waits for a center poke (center LED on), then turns the LED of the
// correct side on and waits for a poke there; a poke on the wrong side is
// reported but doesn't end the wait. Reports [EVENT_TRIAL_END,
// CENTER_OMISSION (no center poke), CENTER_GOT_CORRECT or CENTER_TIMEOUT].

const byte CENTER_C_LED_ON = 1;
const byte CENTER_SIDE_LED_ON = 2;
const byte CENTER_WATER_DELIVERY = 3;
const byte CENTER_OMISSION = 0;
const byte CENTER_GOT_CORRECT = 1;
const byte CENTER_TIMEOUT = 2;

void runCenterInitiated(
  byte correctPort,
  unsigned int cLedOnTimeoutMs,
  unsigned int ledOnTimeoutMs,
  unsigned int valveTimeMs
) {
  unsigned long t0 = millis();

  // --- center poke ---
  sendEvent(EVENT_STATE, CENTER_C_LED_ON, 0);
  digitalWrite(ledPinCenter, HIGH);
  bool gotCenterPoke = false;
  unsigned long cLedOnStart = millis();
  while (millis() - cLedOnStart < cLedOnTimeoutMs) {
    if (pokedCenter()) {
      sendEvent(EVENT_POKE, CENTER_PORT, millis() - t0);
      gotCenterPoke = true;
      break;
    }
  }
  digitalWrite(ledPinCenter, LOW);

  if (!gotCenterPoke) {
    sendEvent(EVENT_TRIAL_END, CENTER_OMISSION, millis() - t0);
    return;
  }

  // --- side response ---
  byte correctLedPin = ledPinOf(correctPort);
  sendEvent(EVENT_STATE, CENTER_SIDE_LED_ON, millis() - t0);
  digitalWrite(correctLedPin, HIGH);
  resetSidePokes();
  bool gotCorrect = false;
  byte pokedPort = 0;
  unsigned long ledOnStart = millis();
  while (millis() - ledOnStart < ledOnTimeoutMs) {
    if (readNewSidePoke(pokedPort)) {
      sendEvent(EVENT_POKE, pokedPort, millis() - t0);
      if (pokedPort == correctPort) {
        gotCorrect = true;
        break;
      }
    }
  }
  digitalWrite(correctLedPin, LOW);

  if (gotCorrect) {
    sendEvent(EVENT_STATE, CENTER_WATER_DELIVERY, millis() - t0);
    deliverWater(correctPort, valveTimeMs);
  }

  sendEvent(
    EVENT_TRIAL_END,
    gotCorrect ? CENTER_GOT_CORRECT : CENTER_TIMEOUT,
    millis() - t0
  );
}

// === Introduce penalty (arduino_5_introduce_penalty.py) ===================
//
// [CMD_INTRODUCE_PENALTY, correct_port, c_led_on_timeout_ms (uint16, LE),
//  led_on_timeout_ms (uint16, LE), valve_time_ms (uint16, LE)]
// Like center initiated, but the first side poke decides the outcome: the
// wrong side is an error. The penalty buzzer is played by the Pi once it
// sees the outcome. Reports [EVENT_TRIAL_END, PENALTY_OMISSION,
// PENALTY_CORRECT, PENALTY_INCORRECT or PENALTY_MISS].

const byte PENALTY_C_LED_ON = 1;
const byte PENALTY_SIDE_LED_ON = 2;
const byte PENALTY_WATER_DELIVERY = 3;
const byte PENALTY_OMISSION = 0;
const byte PENALTY_CORRECT = 1;
const byte PENALTY_INCORRECT = 2;
const byte PENALTY_MISS = 3;

void runIntroducePenalty(
  byte correctPort,
  unsigned int cLedOnTimeoutMs,
  unsigned int ledOnTimeoutMs,
  unsigned int valveTimeMs
) {
  unsigned long t0 = millis();

  // --- center poke ---
  sendEvent(EVENT_STATE, PENALTY_C_LED_ON, 0);
  digitalWrite(ledPinCenter, HIGH);
  bool gotCenterPoke = false;
  unsigned long cLedOnStart = millis();
  while (millis() - cLedOnStart < cLedOnTimeoutMs) {
    if (pokedCenter()) {
      sendEvent(EVENT_POKE, CENTER_PORT, millis() - t0);
      gotCenterPoke = true;
      break;
    }
  }
  digitalWrite(ledPinCenter, LOW);

  if (!gotCenterPoke) {
    sendEvent(EVENT_TRIAL_END, PENALTY_OMISSION, millis() - t0);
    return;
  }

  // --- side response: whichever port is poked first decides the outcome ---
  byte correctLedPin = ledPinOf(correctPort);
  sendEvent(EVENT_STATE, PENALTY_SIDE_LED_ON, millis() - t0);
  digitalWrite(correctLedPin, HIGH);
  byte outcome = PENALTY_MISS;
  byte pokedPort = 0;
  unsigned long ledOnStart = millis();
  while (millis() - ledOnStart < ledOnTimeoutMs) {
    if (readSidePoke(pokedPort)) {
      sendEvent(EVENT_POKE, pokedPort, millis() - t0);
      outcome = (pokedPort == correctPort) ? PENALTY_CORRECT : PENALTY_INCORRECT;
      break;
    }
  }
  digitalWrite(correctLedPin, LOW);

  if (outcome == PENALTY_CORRECT) {
    sendEvent(EVENT_STATE, PENALTY_WATER_DELIVERY, millis() - t0);
    deliverWater(correctPort, valveTimeMs);
  }

  sendEvent(EVENT_TRIAL_END, outcome, millis() - t0);
}

// === Delay (arduino_6_delay.py) ===========================================
//
// [CMD_DELAY, first_port, c_led_on_timeout_ms (uint16, LE),
//  delay_ms (uint16, LE), total_timeout_ms (uint16, LE),
//  valve_time_ms (uint16, LE)]
// After a center poke, lights first_port alone for delay_ms, then both side
// ports until total_timeout_ms; the first side poke decides the outcome
// (first_port is correct). Reports [EVENT_TRIAL_END, DELAY_OMISSION,
// DELAY_CORRECT, DELAY_INCORRECT or DELAY_MISS].

const byte DELAY_C_LED_ON = 1;
const byte DELAY_FIRST_SIDE_LED = 2;
const byte DELAY_BOTH_SIDE_LEDS = 3;
const byte DELAY_CORRECT_CHOICE = 4;
const byte DELAY_OMISSION = 0;
const byte DELAY_CORRECT = 1;
const byte DELAY_INCORRECT = 2;
const byte DELAY_MISS = 3;

void runDelay(
  byte firstPort,
  unsigned int cLedOnTimeoutMs,
  unsigned int delayMs,
  unsigned int totalTimeoutMs,
  unsigned int valveTimeMs
) {
  unsigned long t0 = millis();
  byte secondPort = (firstPort == LEFT_PORT) ? RIGHT_PORT : LEFT_PORT;
  byte firstLedPin = ledPinOf(firstPort);
  byte secondLedPin = ledPinOf(secondPort);

  // --- center poke, up to cLedOnTimeoutMs; none -> omission ---
  sendEvent(EVENT_STATE, DELAY_C_LED_ON, 0);
  digitalWrite(ledPinCenter, HIGH);
  bool gotCenterPoke = false;
  while (millis() - t0 < cLedOnTimeoutMs) {
    if (pokedCenter()) {
      gotCenterPoke = true;
      break;
    }
  }
  digitalWrite(ledPinCenter, LOW);
  if (!gotCenterPoke) {
    sendEvent(EVENT_TRIAL_END, DELAY_OMISSION, millis() - t0);
    return;
  }
  sendEvent(EVENT_POKE, CENTER_PORT, millis() - t0);

  // --- first cue: only firstPort is lit, up to delayMs ---
  sendEvent(EVENT_STATE, DELAY_FIRST_SIDE_LED, millis() - t0);
  digitalWrite(firstLedPin, HIGH);
  unsigned long cueStart = millis();
  byte pokedPort = 0;
  bool responded = false;
  while (millis() - cueStart < delayMs) {
    if (readSidePoke(pokedPort)) {
      responded = true;
      break;
    }
  }

  // --- second cue: both ports lit, up to the overall response window ---
  if (!responded) {
    sendEvent(EVENT_STATE, DELAY_BOTH_SIDE_LEDS, millis() - t0);
    digitalWrite(secondLedPin, HIGH);
    while (millis() - cueStart < totalTimeoutMs) {
      if (readSidePoke(pokedPort)) {
        responded = true;
        break;
      }
    }
  }

  digitalWrite(firstLedPin, LOW);
  digitalWrite(secondLedPin, LOW);

  byte outcome;
  if (!responded) {
    outcome = DELAY_MISS;
  } else {
    sendEvent(EVENT_POKE, pokedPort, millis() - t0);
    outcome = (pokedPort == firstPort) ? DELAY_CORRECT : DELAY_INCORRECT;
    if (outcome == DELAY_CORRECT) {
      sendEvent(EVENT_STATE, DELAY_CORRECT_CHOICE, millis() - t0);
      deliverWater(firstPort, valveTimeMs);
    }
  }

  sendEvent(EVENT_TRIAL_END, outcome, millis() - t0);
}

// === Water calibration (water_calibration_arduino.py) =====================
//
// [CMD_OPEN_VALVE, port, time_us (uint32, LE)]
// Opens the valve of that port for time_us microseconds, timed with
// micros() so the USB latency does not change the volume delivered, and
// reports [EVENT_VALVE_CLOSED, port, elapsed_us] once it is closed again
// (elapsed_us is 0 if the port has no valve).

void openValve(byte port, unsigned long timeUs) {
  if (port != LEFT_PORT && port != RIGHT_PORT) {
    sendEvent(EVENT_VALVE_CLOSED, port, 0);
    return;
  }
  byte valvePin = valvePinOf(port);
  unsigned long t0 = micros();
  digitalWrite(valvePin, HIGH);
  while (micros() - t0 < timeUs) {
  }
  digitalWrite(valvePin, LOW);
  sendEvent(EVENT_VALVE_CLOSED, port, micros() - t0);
}
