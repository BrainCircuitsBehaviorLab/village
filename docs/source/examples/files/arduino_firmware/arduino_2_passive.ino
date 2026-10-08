// Passive learning, Water Delivery Task firmware.
// Companion sketch for arduino_2_passive.py.
//
// The Pi tells this sketch which port gets the reward and the two timings
// it needs at the start of the trial; from there this sketch runs the
// whole trial by itself (open the valve, keep the LED on, wait for a
// response) and only reports back what happened, with its own
// millis()-based timing.
//
// Protocol:
//   Pi -> Arduino, 6 raw bytes, once per trial:
//     [CMD_START_TRIAL, port,
//      valve_time_ms (uint16, little-endian), led_on_timeout_ms (uint16, LE)]
//   Arduino -> Pi, 6 raw bytes per message:
//     [EVENT_POKE, port, elapsed_ms (uint32, little-endian)]
//       -- once per poke seen on EITHER port during the response window.
//          Only a poke on the correct port ends the window early; a poke
//          on the wrong port is reported too, but this sketch keeps
//          waiting.
//     [EVENT_STATE, state, elapsed_ms (uint32, little-endian)]
//       -- every time this sketch enters a new state (see the STATE_*
//          constants), so the Pi can register it with register_enter_state.
//     [EVENT_TRIAL_END, result, elapsed_ms (uint32, little-endian)]
//       -- once, when the response window is over: RESULT_GOT_CORRECT if
//          the correct port was poked before the timeout (whether or not
//          a wrong poke happened earlier), RESULT_TIMEOUT if it never was.
//   elapsed_ms is milliseconds since this sketch received CMD_START_TRIAL
//   for the current trial (its own timer, reset every trial). It is the
//   controller clock: the Pi registers the trial start as controller time 0
//   at the moment it sent that command, and every elapsed_ms as a
//   controller timestamp, so the two clocks never need to be synchronized.
//
// Only ports 1 (left) and 3 (right) are wired. Baud rate must match
// BAUDRATE in arduino_2_passive.py (9600).

const byte CMD_START_TRIAL = 1;

const byte EVENT_POKE = 1;
const byte EVENT_TRIAL_END = 2;
const byte EVENT_STATE = 3;

// States (same names as bpod_2_passive.py; the ITI is done by the Pi)
const byte STATE_WATER_DELIVERY = 1;
const byte STATE_LED_ON = 2;

const byte RESULT_TIMEOUT = 0;
const byte RESULT_GOT_CORRECT = 1;

const byte LEFT_PORT = 1;
const byte RIGHT_PORT = 3;

const byte pokePinLeft = 22;
const byte pokePinRight = 26;
const byte valvePinLeft = 39;
const byte valvePinRight = 43;
const byte ledPinLeft = 23;
const byte ledPinRight = 27;

// Edge state for each poke pin, so a poke that's held down only reports
// once, and a second, separate poke on the same pin still gets reported.
bool lastPokeLeft = false;
bool lastPokeRight = false;

void setup() {
  Serial.begin(9600);
  pinMode(pokePinLeft, INPUT);
  pinMode(pokePinRight, INPUT);
  pinMode(valvePinLeft, OUTPUT);
  pinMode(valvePinRight, OUTPUT);
  pinMode(ledPinLeft, OUTPUT);
  pinMode(ledPinRight, OUTPUT);
  digitalWrite(valvePinLeft, LOW);
  digitalWrite(valvePinRight, LOW);
  digitalWrite(ledPinLeft, LOW);
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

// Rising-edge check on both poke pins -- see arduino_3_active.ino for
// the full explanation; reports at most one newly-poked port per call,
// but is meant to be called every loop iteration.
bool readNewPoke(byte &port) {
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

void runTrial(byte port, unsigned int valveTimeMs, unsigned int ledOnTimeoutMs) {
  unsigned long t0 = millis();

  byte ledPin = (port == LEFT_PORT) ? ledPinLeft : ledPinRight;
  byte valvePin = (port == LEFT_PORT) ? valvePinLeft : valvePinRight;

  // Reward is delivered up front, unconditionally.
  sendEvent(EVENT_STATE, STATE_WATER_DELIVERY, 0);
  digitalWrite(ledPin, HIGH);
  digitalWrite(valvePin, HIGH);
  delay(valveTimeMs);
  digitalWrite(valvePin, LOW);

  // LED stays on for the response window. A poke on the wrong port is
  // reported but doesn't end the wait -- only the correct port (or
  // running out of time) does.
  sendEvent(EVENT_STATE, STATE_LED_ON, millis() - t0);
  lastPokeLeft = digitalRead(pokePinLeft) == HIGH;
  lastPokeRight = digitalRead(pokePinRight) == HIGH;
  bool gotCorrect = false;
  byte pokedPort = 0;
  unsigned long ledOnStart = millis();
  while (millis() - ledOnStart < ledOnTimeoutMs) {
    if (readNewPoke(pokedPort)) {
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
    gotCorrect ? RESULT_GOT_CORRECT : RESULT_TIMEOUT,
    millis() - t0
  );
}

void loop() {
  if (Serial.available() >= 6) {
    byte command = Serial.read();
    if (command == CMD_START_TRIAL) {
      byte port = Serial.read();
      unsigned int valveTimeMs = (unsigned int)Serial.read();
      valveTimeMs |= ((unsigned int)Serial.read()) << 8;
      unsigned int ledOnTimeoutMs = (unsigned int)Serial.read();
      ledOnTimeoutMs |= ((unsigned int)Serial.read()) << 8;

      runTrial(port, valveTimeMs, ledOnTimeoutMs);
    }
  }
}
