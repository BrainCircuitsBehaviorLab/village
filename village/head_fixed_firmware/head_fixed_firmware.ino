// =====================================================================
//  HeadFixed firmware v0.3  —  RP2354 (Arduino core "arduino-pico")
//
//  - Electromagnet (Q3, GPIO21) with power set by PWM at 20 kHz.
//  - Servo (J3, GPIO17): angle 0-180 (1-2 ms pulse, as the Village
//    motors), optionally ramped over a given time.
//  - 2 lickports (GPIO26/27, 4N25 outputs) read with the ADC,
//    threshold with hysteresis and debounce (configurable per port).
//  - Each lick is reported over USB and mirrored to the Bpod outputs
//    (GPIO28/29, polarity set by BPOD_EVENT_IS_LOW; by default
//    idle = 0 V, lick = 3.3 V, which Bpod reads as Port Out / Port In).
//  - Electromagnet safety, in independent layers:
//      1. Absolute limit of 10 min on (main loop).
//      2. Hardware backup alarm that switches it off even if the
//         main loop fails.
//      3. Hardware watchdog: if the MCU hangs it resets (500 ms) and
//         boots with the magnet off.
//      4. A release shorter than 5 s does not reset the 10 min counter
//         (a quick OFF/ON cannot be used to extend the fixation).
//      5. After a timeout, MAG is refused for 30 s.
//
//  USB protocol (text, one command per line, terminated by \n):
//    MAG <power>   power in % (0–100, decimals allowed). 0 = off.
//                  Switching on always starts with a 200 ms kick at
//                  min(100, MAG_KICK_MAX_PCT) % and then drops to
//                  <power> (clamped to MAG_MAX_ALLOWED_PCT) automatically.
//                  If already on, it only changes the power
//                  (does not reset the 10 min counter).
//    OFF           switch the electromagnet off.
//    SERVO <angle> [time_ms]
//                  move the servo to <angle> (0-180), taking time_ms
//                  (0 or omitted = straight there). It keeps holding.
//    SERVO_OFF     stop the servo pulses (releases its holding torque).
//    PING          replies PONG (connection check).
//    STATUS        full state on one line.
//    HELP          list of commands.
//
//  Unsolicited messages sent by the board:
//    LICK <1|2> <1|0> <t_ms>        lick starts / ends
//    MAG_ON <power> <t_ms>
//    MAG_POWER <power> <t_ms>       power changed while on
//    MAG_OFF <reason> <t_ms>        reason: CMD | TIMEOUT | BACKUP
//    SERVO <angle> <time_ms> <t_ms> move accepted
//    SERVO_OFF <t_ms>
//    BOOT <POWERON|WATCHDOG>
// =====================================================================

#include <Arduino.h>
#include <Servo.h>
#include "hardware/pwm.h"
#include "hardware/gpio.h"
#include "hardware/clocks.h"
#include "hardware/watchdog.h"
#include "pico/time.h"

// ------------------------- pins -------------------------------------
const uint8_t PIN_LICK[2] = {26, 27};   // ADC0, ADC1  (J6 L1, L2)
const uint8_t PIN_BPOD[2] = {28, 29};   // J5, J7 -> Bpod port boards
const uint8_t PIN_MAGNET  = 21;         // Q3 gate (J4)
const uint8_t PIN_SERVO   = 17;         // J3 signal
const bool    BPOD_EVENT_IS_LOW = false; // false: lick=3.3V, idle=0V. true: lick=0V, idle=3.3V

// ------------------- safety (do NOT increase these) -----------------
const uint32_t MAG_MAX_ON_MS     = 10UL * 60UL * 1000UL; // 10 min, absolute limit
const uint32_t BACKUP_MARGIN_MS  = 500;    // backup alarm fires 0.5 s later
const uint32_t MIN_RELEASE_MS    = 5000;   // minimum release to reset the counter
const uint32_t LOCKOUT_MS        = 30000;  // after a timeout, MAG blocked for 30 s
const uint32_t WDT_MS            = 500;    // hardware watchdog

// ------------------- electromagnet drive ----------------------------
const uint32_t PWM_FREQ_HZ = 20000;   // above the audible range
const uint16_t PWM_RANGE   = 1000;    // level 0..1000 = 0..100.0 %
const uint32_t KICK_MS     = 200;     // short kick at switch-on
const float    MAG_MAX_ALLOWED_PCT = 40.0f; // hard cap for hold power
const float    MAG_KICK_MAX_PCT    = 60.0f; // hard cap for kick power

// ------------------- servo -------------------------------------------
// 0-180 degrees -> 1-2 ms pulse, the same mapping as the Village motors.
const uint16_t SERVO_MIN_US = 1000;
const uint16_t SERVO_MAX_US = 2000;

// ------------------- lick detection ---------------------------------
// On this board the 4N25 emitter goes to the GPIO with 10k to ground
// (R7/R21) and the collector to 3V3: during a lick the opto LED turns on
// and the pin goes HIGH.
// Tune with STATUS: check raw1/raw2 without and with licking.
const bool     LICK_ACTIVE_LOW       = false;            // true if the pin voltage drops during a lick
const uint16_t LICK_THR_ON[2]        = {2600, 2600};    // [L1, L2] "activity" 0..4095 to start a lick
const uint16_t LICK_THR_OFF[2]       = {1500, 1500};    // [L1, L2] below this the lick ends (hysteresis)
const uint32_t LICK_DEBOUNCE_US[2]   = {50, 100};    // [L1, L2] the change must last this long

// ------------------------- state ------------------------------------
enum MagState : uint8_t { MAG_IDLE, MAG_KICK, MAG_HOLD };
volatile MagState magState = MAG_IDLE;
uint16_t holdLevel        = 0;      // PWM level in HOLD
uint64_t magOnSince_us    = 0;      // start of the current fixation (10 min counter)
uint64_t kickUntil_us     = 0;
uint64_t offSince_us      = 0;      // when it was last switched off
uint32_t accumulatedOn_ms = 0;      // time already used if switched on again quickly
uint64_t lockoutUntil_us  = 0;
volatile bool backupFired = false;
alarm_id_t backupAlarm    = 0;

bool     lickState[2]      = {false, false};
uint64_t lickPending_us[2] = {0, 0};
uint16_t lickRaw[2]        = {0, 0};
uint32_t droppedMsgs       = 0;

Servo    servo;
bool     servoOn          = false;  // pulses being sent
float    servoAngle       = -1.0f;  // last angle written (-1: unknown, at boot)
float    servoFrom        = 0.0f;   // ramp start angle
float    servoTarget      = 0.0f;
uint64_t servoRampStart_us = 0;
uint32_t servoRampMs      = 0;      // 0: no ramp in progress

char     rxBuf[64];
uint8_t  rxLen = 0;

// ------------------------- utilities --------------------------------
static inline uint64_t now_us() { return time_us_64(); }
static inline uint32_t now_ms() { return (uint32_t)(time_us_64() / 1000ULL); }
static inline uint8_t bpodLevel(bool lickActive) {
  return BPOD_EVENT_IS_LOW ? (lickActive ? LOW : HIGH) : (lickActive ? HIGH : LOW);
}

// Sends a line only if it fits in the USB buffer: never blocks the loop
// (if it blocked, the watchdog would reset the board).
void sendLine(const char *s) {
  size_t n = strlen(s) + 2;
  if (Serial && (size_t)Serial.availableForWrite() >= n) {
    Serial.print(s);
    Serial.print("\r\n");
  } else {
    droppedMsgs++;
  }
}

// ------------------------- electromagnet ----------------------------
// "Hard" off: makes the pin a plain GPIO driven low. Safe to call from an IRQ.
void magnetHardOff() {
  pwm_set_gpio_level(PIN_MAGNET, 0);
  gpio_init(PIN_MAGNET);
  gpio_pull_down(PIN_MAGNET);   // internal pull-down (~50k): this board has no external one on the Q3 gate
  gpio_set_dir(PIN_MAGNET, GPIO_OUT);
  gpio_put(PIN_MAGNET, 0);
}

void magnetSetLevel(uint16_t level) {
  if (level == 0) { magnetHardOff(); return; }
  gpio_set_function(PIN_MAGNET, GPIO_FUNC_PWM);
  pwm_set_gpio_level(PIN_MAGNET, level);   // level >= PWM_RANGE -> 100 %
}

// Backup alarm: runs in an interrupt, independent of the main loop.
int64_t backupKill(alarm_id_t, void *) {
  magnetHardOff();
  magState = MAG_IDLE;
  backupFired = true;
  return 0;  // do not repeat
}

void magnetOff(const char *reason) {
  if (backupAlarm > 0) { cancel_alarm(backupAlarm); backupAlarm = 0; }
  bool wasOn = (magState != MAG_IDLE);
  magnetHardOff();
  if (wasOn) {
    accumulatedOn_ms = (uint32_t)((now_us() - magOnSince_us) / 1000ULL);
    offSince_us = now_us();
  }
  magState = MAG_IDLE;
  char b[48];
  snprintf(b, sizeof b, "MAG_OFF %s %lu", reason, (unsigned long)now_ms());
  sendLine(b);
}

void magnetOn(float pct) {
  uint64_t t = now_us();
  if (t < lockoutUntil_us) {
    char b[48];
    snprintf(b, sizeof b, "ERR LOCKOUT %lu",
             (unsigned long)((lockoutUntil_us - t) / 1000ULL));
    sendLine(b);
    return;
  }
  if (pct > 100.0f) pct = 100.0f;
  if (pct > MAG_MAX_ALLOWED_PCT) pct = MAG_MAX_ALLOWED_PCT;
  holdLevel = (uint16_t)(pct * (PWM_RANGE / 100.0f) + 0.5f);
  const uint16_t kickLevel = (uint16_t)(min(100.0f, MAG_KICK_MAX_PCT) * (PWM_RANGE / 100.0f) + 0.5f);

  if (magState != MAG_IDLE) {          // already on: only change the power
    if (magState == MAG_HOLD) magnetSetLevel(holdLevel);
    char b[48];
    snprintf(b, sizeof b, "MAG_POWER %.1f %lu", pct, (unsigned long)now_ms());
    sendLine(b);
    return;
  }

  // Was the release long enough? If not, keep counting the previous time.
  uint32_t already = 0;
  if (offSince_us != 0 && (t - offSince_us) < (uint64_t)MIN_RELEASE_MS * 1000ULL)
    already = accumulatedOn_ms;
  if (already >= MAG_MAX_ON_MS) {
    lockoutUntil_us = t + (uint64_t)LOCKOUT_MS * 1000ULL;
    sendLine("ERR MAX_TIME");
    return;
  }
  magOnSince_us = t - (uint64_t)already * 1000ULL;

  backupFired = false;
  backupAlarm = add_alarm_in_ms(MAG_MAX_ON_MS - already + BACKUP_MARGIN_MS,
                                backupKill, nullptr, true);
  if (backupAlarm <= 0) {              // never switch on without the backup alarm
    sendLine("ERR NO_BACKUP_ALARM");
    return;
  }
  kickUntil_us = t + (uint64_t)KICK_MS * 1000ULL;
  magState = MAG_KICK;
  magnetSetLevel(kickLevel);           // kick is capped by MAG_KICK_MAX_PCT
  char b[64];
  snprintf(b, sizeof b, "MAG_ON %.1f %lu remaining_ms=%lu", pct,
           (unsigned long)now_ms(), (unsigned long)(MAG_MAX_ON_MS - already));
  sendLine(b);
}

void magnetUpdate() {
  if (backupFired) {                   // the alarm already switched it off from the IRQ
    backupFired = false;
    backupAlarm = 0;
    accumulatedOn_ms = MAG_MAX_ON_MS;
    offSince_us = now_us();
    lockoutUntil_us = now_us() + (uint64_t)LOCKOUT_MS * 1000ULL;
    char b[40];
    snprintf(b, sizeof b, "MAG_OFF BACKUP %lu", (unsigned long)now_ms());
    sendLine(b);
    return;
  }
  if (magState == MAG_IDLE) return;
  uint64_t t = now_us();

  if (t - magOnSince_us >= (uint64_t)MAG_MAX_ON_MS * 1000ULL) {
    magnetOff("TIMEOUT");
    lockoutUntil_us = now_us() + (uint64_t)LOCKOUT_MS * 1000ULL;
    return;
  }
  if (magState == MAG_KICK && t >= kickUntil_us) {
    magState = MAG_HOLD;
    magnetSetLevel(holdLevel);
  }
}

// ------------------------- lickports --------------------------------
void lickUpdate() {
  uint64_t t = now_us();
  for (int i = 0; i < 2; i++) {
    uint16_t raw = analogRead(PIN_LICK[i]);
    lickRaw[i] = raw;
    uint16_t act = LICK_ACTIVE_LOW ? (4095 - raw) : raw;
    bool want = lickState[i] ? (act > LICK_THR_OFF[i]) : (act > LICK_THR_ON[i]);
    if (want == lickState[i]) { lickPending_us[i] = 0; continue; }
    if (lickPending_us[i] == 0) { lickPending_us[i] = t; continue; }
    if (t - lickPending_us[i] < LICK_DEBOUNCE_US[i]) continue;

    lickState[i] = want;
    lickPending_us[i] = 0;
    digitalWrite(PIN_BPOD[i], bpodLevel(want));
    char b[40];
    snprintf(b, sizeof b, "LICK %d %d %lu", i + 1, want ? 1 : 0, (unsigned long)now_ms());
    sendLine(b);
  }
}

// ------------------------- servo ------------------------------------
void servoWrite(float angle) {
  servo.writeMicroseconds((int)(SERVO_MIN_US + angle * (SERVO_MAX_US - SERVO_MIN_US) / 180.0f + 0.5f));
  servoAngle = angle;
}

// The real position is unknown at boot (servoAngle < 0): the first move
// goes straight to the target, the next ones ramp from the last angle.
void servoMove(float angle, uint32_t time_ms) {
  if (angle < 0.0f) angle = 0.0f;
  if (angle > 180.0f) angle = 180.0f;
  if (!servoOn) {
    servo.attach(PIN_SERVO, SERVO_MIN_US, SERVO_MAX_US);
    servoOn = true;
  }
  if (time_ms == 0 || servoAngle < 0.0f) {
    servoRampMs = 0;
    servoWrite(angle);
  } else {
    servoFrom = servoAngle;
    servoTarget = angle;
    servoRampStart_us = now_us();
    servoRampMs = time_ms;
  }
  char b[48];
  snprintf(b, sizeof b, "SERVO %.1f %lu %lu", angle, (unsigned long)time_ms,
           (unsigned long)now_ms());
  sendLine(b);
}

void servoOff() {
  servoRampMs = 0;
  if (servoOn) {
    servo.detach();
    servoOn = false;
  }
  char b[32];
  snprintf(b, sizeof b, "SERVO_OFF %lu", (unsigned long)now_ms());
  sendLine(b);
}

void servoUpdate() {
  if (servoRampMs == 0) return;
  uint64_t elapsed_us = now_us() - servoRampStart_us;
  if (elapsed_us >= (uint64_t)servoRampMs * 1000ULL) {
    servoRampMs = 0;
    servoWrite(servoTarget);
    return;
  }
  float f = (float)elapsed_us / (servoRampMs * 1000.0f);
  servoWrite(servoFrom + (servoTarget - servoFrom) * f);
}

// ------------------------- commands ---------------------------------
void sendStatus() {
  static const char *names[] = {"OFF", "KICK", "HOLD"};
  uint64_t t = now_us();
  uint32_t onMs = (magState == MAG_IDLE) ? 0 : (uint32_t)((t - magOnSince_us) / 1000ULL);
  uint32_t lock = (t < lockoutUntil_us) ? (uint32_t)((lockoutUntil_us - t) / 1000ULL) : 0;
  char servoStr[12];
  if (servoOn) snprintf(servoStr, sizeof servoStr, "%.1f", servoAngle);
  else snprintf(servoStr, sizeof servoStr, "OFF");
  char b[220];
  snprintf(b, sizeof b,
           "STATUS mag=%s power=%.1f on_ms=%lu remaining_ms=%lu lockout_ms=%lu "
           "servo=%s L1=%d L2=%d raw1=%u raw2=%u dropped=%lu",
           names[magState], holdLevel * (100.0f / PWM_RANGE),
           (unsigned long)onMs,
           (unsigned long)(magState == MAG_IDLE ? 0 : MAG_MAX_ON_MS - onMs),
           (unsigned long)lock, servoStr, lickState[0], lickState[1],
           lickRaw[0], lickRaw[1], (unsigned long)droppedMsgs);
  sendLine(b);
}

void handleLine(char *line) {
  for (char *p = line; *p; p++) *p = toupper(*p);
  if (strncmp(line, "MAG", 3) == 0) {
    float pct = atof(line + 3);
    if (pct <= 0.0f) magnetOff("CMD"); else magnetOn(pct);
  } else if (strcmp(line, "OFF") == 0) {
    magnetOff("CMD");
  } else if (strcmp(line, "SERVO_OFF") == 0) {
    servoOff();
  } else if (strncmp(line, "SERVO", 5) == 0) {
    float angle = 0.0f;
    unsigned long time_ms = 0;
    if (sscanf(line + 5, "%f %lu", &angle, &time_ms) >= 1) servoMove(angle, time_ms);
    else sendLine("ERR SERVO");
  } else if (strcmp(line, "PING") == 0) {
    sendLine("PONG");
  } else if (strcmp(line, "STATUS") == 0) {
    sendStatus();
  } else if (strcmp(line, "HELP") == 0) {
    char b[144];
    snprintf(b, sizeof b,
             "CMDS: MAG <0-100> (hold<=%.1f, kick<=%.1f) | OFF | "
             "SERVO <0-180> [time_ms] | SERVO_OFF | PING | STATUS | HELP",
             MAG_MAX_ALLOWED_PCT, MAG_KICK_MAX_PCT);
    sendLine(b);
  } else if (line[0] != 0) {
    sendLine("ERR UNKNOWN");
  }
}

void serialUpdate() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') { rxBuf[rxLen] = 0; handleLine(rxBuf); rxLen = 0; continue; }
    if (rxLen < sizeof(rxBuf) - 1) rxBuf[rxLen++] = c;
    else rxLen = 0;                      // line too long: discarded
  }
}

// ------------------------- setup / loop -----------------------------
void setup() {
  magnetHardOff();                       // first thing: electromagnet off

  for (int i = 0; i < 2; i++) {          // Bpod lines: idle/event polarity from BPOD_EVENT_IS_LOW
    pinMode(PIN_BPOD[i], OUTPUT);
    digitalWrite(PIN_BPOD[i], bpodLevel(false));
  }

  // Electromagnet PWM: 20 kHz, 1000 steps
  uint slice = pwm_gpio_to_slice_num(PIN_MAGNET);
  pwm_config cfg = pwm_get_default_config();
  pwm_config_set_wrap(&cfg, PWM_RANGE - 1);
  pwm_config_set_clkdiv(&cfg, (float)clock_get_hz(clk_sys) / (PWM_FREQ_HZ * (float)PWM_RANGE));
  pwm_init(slice, &cfg, true);
  pwm_set_gpio_level(PIN_MAGNET, 0);
  magnetHardOff();

  analogReadResolution(12);

  bool wdReset = watchdog_caused_reboot();
  watchdog_enable(WDT_MS, true);

  Serial.begin(115200);                  // USB CDC (baud rate is irrelevant)
  sendLine(wdReset ? "BOOT WATCHDOG" : "BOOT POWERON");
}

void loop() {
  watchdog_update();
  serialUpdate();
  magnetUpdate();
  servoUpdate();
  lickUpdate();
}
