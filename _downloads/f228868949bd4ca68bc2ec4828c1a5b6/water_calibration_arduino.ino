// Water calibration firmware.
// Companion sketch for water_calibration_arduino.py.
//
// The Pi asks this sketch to open one valve for a given time; this sketch
// times the opening itself, with micros(), so the USB latency does not
// change the volume delivered, and reports back when the valve is closed.
//
// Protocol:
//   Pi -> Arduino, 6 raw bytes, once per valve opening:
//     [CMD_OPEN_VALVE, port, time_us (uint32, little-endian)]
//   Arduino -> Pi, 6 raw bytes, once the valve is closed again:
//     [EVENT_VALVE_CLOSED, port, elapsed_us (uint32, little-endian)]
//       -- elapsed_us is how long the valve was actually open (0 if the
//          port has no valve).
//
// Baud rate must match BAUDRATE in water_calibration_arduino.py (9600).
//
// If your task firmware already listens for commands, you can add
// CMD_OPEN_VALVE to it instead, so the same sketch serves for the tasks and
// for the calibration.

const byte CMD_OPEN_VALVE = 2;
const byte EVENT_VALVE_CLOSED = 4;

// Valve pin of each port (port 1 = valvePins[0]...). Ports 1 and 3 are
// wired as in the arduino_* examples; adapt the pins to your board.
const byte NUM_PORTS = 3;
const byte valvePins[NUM_PORTS] = {39, 41, 43};

void setup() {
  Serial.begin(9600);
  for (byte i = 0; i < NUM_PORTS; i++) {
    pinMode(valvePins[i], OUTPUT);
    digitalWrite(valvePins[i], LOW);
  }
}

void sendEvent(byte eventCode, byte value, unsigned long elapsed) {
  Serial.write(eventCode);
  Serial.write(value);
  Serial.write((byte)(elapsed & 0xFF));
  Serial.write((byte)((elapsed >> 8) & 0xFF));
  Serial.write((byte)((elapsed >> 16) & 0xFF));
  Serial.write((byte)((elapsed >> 24) & 0xFF));
}

void openValve(byte port, unsigned long timeUs) {
  if (port < 1 || port > NUM_PORTS) {
    sendEvent(EVENT_VALVE_CLOSED, port, 0);
    return;
  }
  byte valvePin = valvePins[port - 1];
  unsigned long t0 = micros();
  digitalWrite(valvePin, HIGH);
  while (micros() - t0 < timeUs) {
  }
  digitalWrite(valvePin, LOW);
  sendEvent(EVENT_VALVE_CLOSED, port, micros() - t0);
}

void loop() {
  if (Serial.available() >= 6) {
    byte command = Serial.read();
    byte port = Serial.read();
    unsigned long timeUs = 0;
    for (byte i = 0; i < 4; i++) {
      timeUs |= ((unsigned long)Serial.read()) << (8 * i);
    }
    if (command == CMD_OPEN_VALVE) {
      openValve(port, timeUs);
    }
  }
}
