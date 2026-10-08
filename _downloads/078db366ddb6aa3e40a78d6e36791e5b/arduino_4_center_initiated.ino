// Center-Initiated Side Alternation Task firmware.
// Companion sketch for arduino_4_center_initiated.py.
//
// The Pi tells this sketch which side is correct and the three timings it
// needs at the start of the trial; from there this sketch runs the whole
// trial (center poke, side poke, valve) by itself and only reports back
// what happened, with its own millis()-based timing.
//
// Protocol:
//   Pi -> Arduino, 8 raw bytes, once per trial:
//     [CMD_START_TRIAL, correct_port,
//      c_led_on_timeout_ms (uint16, little-endian),
//      led_on_timeout_ms (uint16, little-endian),
//      valve_time_ms (uint16, little-endian)]
//   Arduino -> Pi, 6 raw bytes per message:
//     [EVENT_POKE, port, elapsed_ms (uint32, little-endian)]
//       -- once for the center poke, then once per poke seen on EITHER
//          side port during the response window. Only a poke on the
//          correct side ends that window early; a poke on the wrong side
//          is reported too, but this sketch keeps waiting.
//     [EVENT_STATE, state, elapsed_ms (uint32, little-endian)]
//       -- every time this sketch enters a new state (see the STATE_*
//          constants), so the Pi can register it with register_enter_state.
//     [EVENT_TRIAL_END, result, elapsed_ms (uint32, little-endian)]
//       -- once, when the trial is over. RESULT_OMISSION if the center
//          port was never poked (side LEDs never turned on); otherwise
//          RESULT_GOT_CORRECT if the correct side was poked before its
//          timeout (whether or not a wrong poke happened earlier), or
//          RESULT_TIMEOUT if it never was.
//   elapsed_ms is milliseconds since this sketch received CMD_START_TRIAL
//   for the current trial (its own timer, reset every trial). It is the
//   controller clock: the Pi registers the trial start as controller time 0
//   at the moment it sent that command, and every elapsed_ms as a
//   controller timestamp, so the two clocks never need to be synchronized.
//
// 3 ports are wired: 1 (left), 2 (center), 3 (right). Baud rate must match
// BAUDRATE in arduino_4_center_initiated.py (9600).

const byte CMD_START_TRIAL = 1;

const byte EVENT_POKE = 1;
const byte EVENT_TRIAL_END = 2;
const byte EVENT_STATE = 3;

// States (same names as bpod_4_center_initiated.py; the ITI is done by the Pi)
const byte STATE_C_LED_ON = 1;
const byte STATE_SIDE_LED_ON = 2;
const byte STATE_WATER_DELIVERY = 3;

const byte RESULT_OMISSION = 0;
const byte RESULT_GOT_CORRECT = 1;
const byte RESULT_TIMEOUT = 2;

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
// reported. The center pin doesn't need this: it's only ever checked
// once per trial, and the loop exits as soon as it's seen.
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

// Rising-edge check on both side poke pins -- see arduino_3_active.ino
// for the full explanation; reports at most one newly-poked port per
// call, but is meant to be called every loop iteration.
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

void runTrial(
  byte correctPort,
  unsigned int cLedOnTimeoutMs,
  unsigned int ledOnTimeoutMs,
  unsigned int valveTimeMs
) {
  unsigned long t0 = millis();

  // --- center poke ---
  sendEvent(EVENT_STATE, STATE_C_LED_ON, 0);
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
    sendEvent(EVENT_TRIAL_END, RESULT_OMISSION, millis() - t0);
    return;
  }

  // --- side response: a wrong poke is reported but doesn't end the
  // window -- only the correct side (or running out of time) does ---
  byte correctLedPin = (correctPort == LEFT_PORT) ? ledPinLeft : ledPinRight;
  byte correctValvePin = (correctPort == LEFT_PORT) ? valvePinLeft : valvePinRight;

  sendEvent(EVENT_STATE, STATE_SIDE_LED_ON, millis() - t0);
  digitalWrite(correctLedPin, HIGH);
  lastPokeLeft = digitalRead(pokePinLeft) == HIGH;
  lastPokeRight = digitalRead(pokePinRight) == HIGH;
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
    sendEvent(EVENT_STATE, STATE_WATER_DELIVERY, millis() - t0);
    digitalWrite(correctValvePin, HIGH);
    delay(valveTimeMs);
    digitalWrite(correctValvePin, LOW);
  }

  sendEvent(
    EVENT_TRIAL_END,
    gotCorrect ? RESULT_GOT_CORRECT : RESULT_TIMEOUT,
    millis() - t0
  );
}

void loop() {
  if (Serial.available() >= 8) {
    byte command = Serial.read();
    if (command == CMD_START_TRIAL) {
      byte correctPort = Serial.read();
      unsigned int cLedOnTimeoutMs = (unsigned int)Serial.read();
      cLedOnTimeoutMs |= ((unsigned int)Serial.read()) << 8;
      unsigned int ledOnTimeoutMs = (unsigned int)Serial.read();
      ledOnTimeoutMs |= ((unsigned int)Serial.read()) << 8;
      unsigned int valveTimeMs = (unsigned int)Serial.read();
      valveTimeMs |= ((unsigned int)Serial.read()) << 8;

      runTrial(correctPort, cLedOnTimeoutMs, ledOnTimeoutMs, valveTimeMs);
    }
  }
}
