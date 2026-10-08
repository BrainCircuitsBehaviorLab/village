// Delayed Side-Cue Discrimination Task, easy version -- firmware.
// Companion sketch for arduino_6_delay.py.
//
// The Pi tells this sketch which side lights up first, how long to wait
// before lighting the other side too, the overall response window, and
// the valve time for a correct response. From there this sketch runs the
// whole trial (center poke, both cue phases, valve) by itself and only
// reports back what happened, with its own millis()-based timing. The
// penalty buzzer itself is played by the Pi (this board has no speaker)
// once it sees an "incorrect" outcome.
//
// Protocol:
//   Pi -> Arduino, 10 raw bytes, once per trial:
//     [CMD_START_TRIAL, first_port,
//      c_led_on_timeout_ms (uint16, little-endian),
//      delay_ms (uint16, little-endian),
//      total_timeout_ms (uint16, little-endian),
//      valve_time_ms (uint16, little-endian)]
//   Arduino -> Pi, 6 raw bytes per message:
//     [EVENT_POKE, port, elapsed_ms (uint32, little-endian)]
//       -- once per poke that matters (center, then whichever side is
//          poked first)
//     [EVENT_STATE, state, elapsed_ms (uint32, little-endian)]
//       -- every time this sketch enters a new state (see the STATE_*
//          constants), so the Pi can register it with register_enter_state.
//     [EVENT_TRIAL_END, outcome, elapsed_ms (uint32, little-endian)]
//       -- once, when the trial is over
//   elapsed_ms is milliseconds since this sketch received CMD_START_TRIAL
//   for the current trial (its own timer, reset every trial). It is the
//   controller clock: the Pi registers the trial start as controller time 0
//   at the moment it sent that command, and every elapsed_ms as a
//   controller timestamp, so the two clocks never need to be synchronized.
//
// The center-poke wait lasts up to c_led_on_timeout_ms: with no poke, the
// trial ends as an omission, so trials keep advancing even if the animal
// does nothing.
//
// 3 ports are wired: 1 (left), 2 (center), 3 (right). Baud rate must match
// BAUDRATE in arduino_6_delay.py (9600).

const byte CMD_START_TRIAL = 1;

const byte EVENT_POKE = 1;
const byte EVENT_TRIAL_END = 2;
const byte EVENT_STATE = 3;

// States (same names as bpod_6_delay.py; the ITI and the wrong_choice/
// timeout penalty are done by the Pi)
const byte STATE_C_LED_ON = 1;
const byte STATE_FIRST_SIDE_LED = 2;
const byte STATE_BOTH_SIDE_LEDS = 3;
const byte STATE_CORRECT_CHOICE = 4;

const byte OUTCOME_OMISSION = 0;
const byte OUTCOME_CORRECT = 1;
const byte OUTCOME_INCORRECT = 2;
const byte OUTCOME_MISS = 3;

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

void sendEvent(byte eventCode, byte value, unsigned long elapsedMs) {
  Serial.write(eventCode);
  Serial.write(value);
  Serial.write((byte)(elapsedMs & 0xFF));
  Serial.write((byte)((elapsedMs >> 8) & 0xFF));
  Serial.write((byte)((elapsedMs >> 16) & 0xFF));
  Serial.write((byte)((elapsedMs >> 24) & 0xFF));
}

bool pokedCenter() {
  return digitalRead(pokePinCenter) == HIGH;
}

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

void runTrial(
  byte firstPort,
  unsigned int cLedOnTimeoutMs,
  unsigned int delayMs,
  unsigned int totalTimeoutMs,
  unsigned int valveTimeMs
) {
  unsigned long t0 = millis();
  byte secondPort = (firstPort == LEFT_PORT) ? RIGHT_PORT : LEFT_PORT;
  byte firstLedPin = (firstPort == LEFT_PORT) ? ledPinLeft : ledPinRight;
  byte secondLedPin = (secondPort == LEFT_PORT) ? ledPinLeft : ledPinRight;
  byte firstValvePin = (firstPort == LEFT_PORT) ? valvePinLeft : valvePinRight;

  // --- center poke, up to cLedOnTimeoutMs; none -> omission ---
  sendEvent(EVENT_STATE, STATE_C_LED_ON, 0);
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
    sendEvent(EVENT_TRIAL_END, OUTCOME_OMISSION, millis() - t0);
    return;
  }
  sendEvent(EVENT_POKE, CENTER_PORT, millis() - t0);

  // --- first cue: only firstPort is lit, up to delayMs ---
  sendEvent(EVENT_STATE, STATE_FIRST_SIDE_LED, millis() - t0);
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
    sendEvent(EVENT_STATE, STATE_BOTH_SIDE_LEDS, millis() - t0);
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
    outcome = OUTCOME_MISS;
  } else {
    sendEvent(EVENT_POKE, pokedPort, millis() - t0);
    outcome = (pokedPort == firstPort) ? OUTCOME_CORRECT : OUTCOME_INCORRECT;
    if (outcome == OUTCOME_CORRECT) {
      sendEvent(EVENT_STATE, STATE_CORRECT_CHOICE, millis() - t0);
      digitalWrite(firstValvePin, HIGH);
      delay(valveTimeMs);
      digitalWrite(firstValvePin, LOW);
    }
    // OUTCOME_INCORRECT: nothing more to do here, the Pi handles the
    // buzzer and the timeout once it sees this outcome.
  }

  sendEvent(EVENT_TRIAL_END, outcome, millis() - t0);
}

void loop() {
  if (Serial.available() >= 10) {
    byte command = Serial.read();
    if (command == CMD_START_TRIAL) {
      byte firstPort = Serial.read();
      unsigned int cLedOnTimeoutMs = (unsigned int)Serial.read();
      cLedOnTimeoutMs |= ((unsigned int)Serial.read()) << 8;
      unsigned int delayMs = (unsigned int)Serial.read();
      delayMs |= ((unsigned int)Serial.read()) << 8;
      unsigned int totalTimeoutMs = (unsigned int)Serial.read();
      totalTimeoutMs |= ((unsigned int)Serial.read()) << 8;
      unsigned int valveTimeMs = (unsigned int)Serial.read();
      valveTimeMs |= ((unsigned int)Serial.read()) << 8;

      runTrial(firstPort, cLedOnTimeoutMs, delayMs, totalTimeoutMs, valveTimeMs);
    }
  }
}
