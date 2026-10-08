// Habituation Task firmware.
// Companion sketch for arduino_1_habituation.py.
//
// The Pi tells this sketch how long the trial should last; from there this
// sketch watches all 3 poke sensors on its own and reports back either
// whichever port was poked first, or that nobody poked at all, with its
// own millis()-based timing.
//
// Protocol:
//   Pi -> Arduino, 3 raw bytes, once per trial:
//     [CMD_START_TRIAL, duration_s (uint16, little-endian)]
//   Arduino -> Pi, 6 raw bytes per message:
//     [EVENT_STATE, state, elapsed_ms (uint32, little-endian)]
//       -- every time this sketch enters a new state (see the STATE_*
//          constants), so the Pi can register it with register_enter_state.
//     [EVENT_TRIAL_END, port (0 if nobody poked), elapsed_ms (uint32, LE)]
//       -- once, when the trial is over.
//   elapsed_ms is milliseconds since this sketch received CMD_START_TRIAL
//   for the current trial (its own timer, reset every trial). It is the
//   controller clock: the Pi registers the trial start as controller time 0
//   at the moment it sent that command, and every elapsed_ms as a
//   controller timestamp, so the two clocks never need to be synchronized.
//
// 3 ports are wired: 1 (left), 2 (center), 3 (right). Baud rate must match
// BAUDRATE in arduino_1_habituation.py (9600).

const byte CMD_START_TRIAL = 1;
const byte EVENT_TRIAL_END = 1;
const byte EVENT_STATE = 3;

// States (same names as bpod_1_habituation.py)
const byte STATE_READY_TO_EXPLORE = 1;

const byte pokePinLeft = 22;
const byte pokePinCenter = 24;
const byte pokePinRight = 26;

void setup() {
  Serial.begin(9600);
  pinMode(pokePinLeft, INPUT);
  pinMode(pokePinCenter, INPUT);
  pinMode(pokePinRight, INPUT);
}

void sendEvent(byte eventCode, byte value, unsigned long elapsedMs) {
  Serial.write(eventCode);
  Serial.write(value);
  Serial.write((byte)(elapsedMs & 0xFF));
  Serial.write((byte)((elapsedMs >> 8) & 0xFF));
  Serial.write((byte)((elapsedMs >> 16) & 0xFF));
  Serial.write((byte)((elapsedMs >> 24) & 0xFF));
}

byte readPoke() {
  if (digitalRead(pokePinLeft) == HIGH) return 1;
  if (digitalRead(pokePinCenter) == HIGH) return 2;
  if (digitalRead(pokePinRight) == HIGH) return 3;
  return 0;
}

void runTrial(unsigned int durationS) {
  unsigned long t0 = millis();
  unsigned long durationMs = (unsigned long)durationS * 1000UL;
  sendEvent(EVENT_STATE, STATE_READY_TO_EXPLORE, 0);

  byte pokedPort = 0;
  while (millis() - t0 < durationMs) {
    pokedPort = readPoke();
    if (pokedPort != 0) {
      break;
    }
  }

  sendEvent(EVENT_TRIAL_END, pokedPort, millis() - t0);
}

void loop() {
  if (Serial.available() >= 3) {
    byte command = Serial.read();
    if (command == CMD_START_TRIAL) {
      unsigned int durationS = (unsigned int)Serial.read();
      durationS |= ((unsigned int)Serial.read()) << 8;
      runTrial(durationS);
    }
  }
}
