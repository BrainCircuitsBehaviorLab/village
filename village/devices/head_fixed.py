"""Driver of the head-fixed board: an RP2354 board, connected by USB, that
drives the electromagnet that holds the headbar and a servo, and detects the
licks on two lickports.

The licks are not handled here: the board sends each one straight to the
photogate input of a Bpod port board, so the state machine sees it as a Port In
/ Port Out event. They are also reported over USB, and kept in lick_count.

The firmware is in village/head_fixed_firmware. It speaks a text
protocol over the USB serial port, one command per line:

    MAG <0-100>              electromagnet power in % (0 = off)
    OFF                      electromagnet off
    SERVO <0-180> [time_ms]  move the servo, optionally ramped over time_ms
    SERVO_OFF                stop the servo pulses (no holding torque)
    PING / STATUS / HELP

and it sends, unsolicited: LICK <1|2> <1|0> <t_ms>, MAG_ON, MAG_POWER,
MAG_OFF <CMD|TIMEOUT|BACKUP>, SERVO, SERVO_OFF, ERR ..., BOOT <POWERON|WATCHDOG>.

The safety of the electromagnet lives in the firmware, not here: it never stays
on more than 10 minutes, whatever the Raspberry Pi does.
"""

from __future__ import annotations

import threading
import time
import traceback
from collections.abc import Callable

import serial
from serial.tools import list_ports

from village.classes.enums import Active
from village.classes.null_classes import NullHeadFixed
from village.scripts.log import log
from village.settings import settings

# USB vendor ID of the Raspberry Pi RP2040/RP2350 chips (the Arduino core keeps
# it). Bpod uses another one (Teensy), so it is not confused with the board.
RP2_USB_VID = 0x2E8A


class HeadFixed:
    """Controls the head-fixed board through its USB serial port.

    All the commands return immediately: they are sent to the board, which
    does the work (the 200 ms kick of the electromagnet, the servo ramp...).

    Attributes:
        name (str): Name of the device, used in the log.
        port (str): The serial port it is connected to.
        error (str): Error message, "" if the board is connected.
        magnet_on (bool): Whether the electromagnet is on, as last reported by
            the board.
        lick_count (list[int]): Licks detected on lickports 1 and 2 since the
            connection (or since reset_lick_count).
        on_lick (Callable | None): Optional function called on every lick start
            and end, as on_lick(lickport, state, board_ms): lickport 1 or 2,
            state 1 (start) or 0 (end), board_ms the board's clock in ms. It
            runs in the reader thread: keep it fast.
    """

    def __init__(self, port: str) -> None:
        """Opens the serial port and checks that the board answers.

        Args:
            port (str): Serial port path, or "auto" to look for the board
                among the USB serial ports.

        Raises:
            Exception: If the board is not found or does not answer.
        """
        self.name = "head_fixed"
        self.error = ""
        self.magnet_on = False
        self.lick_count = [0, 0]
        self.on_lick: Callable[[int, int, int], None] | None = None
        self._lock = threading.Lock()
        self._status: dict[str, str] | None = None
        self._status_event = threading.Event()
        self._running = True
        if port == "auto":
            self.conn = self._find_board()
        else:
            self.conn = self._open(port)
            if not self._ping(self.conn):
                self.conn.close()
                raise RuntimeError("The board at " + port + " does not answer PING")
        self.port = str(self.conn.port)
        self._connected_at = time.monotonic()
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    # ── Commands ──────────────────────────────────────────────────────────────

    def magnet(self, power: float) -> None:
        """Switches the electromagnet on, or changes its power if it is on.

        It always switches on with a short kick (200 ms) to pull the headbar,
        and then holds at `power`. The firmware caps the power (40 % now) and
        switches it off by itself after 10 minutes.

        Args:
            power (float): Holding power in % (0-100). 0 switches it off.
        """
        if power <= 0:
            self.magnet_off()
        else:
            self._send(f"MAG {power:.1f}")

    def magnet_off(self) -> None:
        """Switches the electromagnet off (the spring releases the headbar)."""
        self._send("OFF")

    def servo(self, angle: float, time_ms: int = 0) -> None:
        """Moves the servo to `angle`.

        The first move after the board starts goes straight to the angle (its
        real position is unknown); the next ones take time_ms to get there.
        The servo keeps holding its position until servo_off.

        Args:
            angle (float): Angle in degrees (0-180).
            time_ms (int): Time to get there, in ms (0: as fast as possible).
        """
        self._send(f"SERVO {angle:.1f} {max(0, int(time_ms))}")

    def servo_off(self) -> None:
        """Stops the servo pulses: it releases its holding torque."""
        self._send("SERVO_OFF")

    def status(self, timeout: float = 1.0) -> dict[str, str] | None:
        """Asks the board for its state.

        Args:
            timeout (float): Seconds to wait for the reply.

        Returns:
            dict[str, str] | None: The fields of the STATUS line (mag, power,
            on_ms, remaining_ms, lockout_ms, servo, L1, L2, raw1, raw2,
            dropped), or None if there was no reply.
        """
        self._status_event.clear()
        self._send("STATUS")
        if self._status_event.wait(timeout):
            return self._status
        return None

    def reset_lick_count(self) -> None:
        """Sets lick_count back to [0, 0]."""
        self.lick_count = [0, 0]

    def close(self) -> None:
        """Switches the electromagnet off and closes the serial port."""
        try:
            self.magnet_off()
        finally:
            self._running = False
            time.sleep(0.1)
            try:
                self.conn.close()
            except Exception:
                pass

    # ── Connection ────────────────────────────────────────────────────────────

    @staticmethod
    def _open(port: str) -> serial.Serial:
        return serial.Serial(port, 115200, timeout=0.1, write_timeout=1)

    @staticmethod
    def _ping(conn: serial.Serial, timeout: float = 1.0) -> bool:
        """Whether the board on `conn` answers PONG to a PING."""
        conn.reset_input_buffer()
        conn.write(b"PING\n")
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if conn.readline().decode(errors="ignore").strip() == "PONG":
                return True
        return False

    def _find_board(self) -> serial.Serial:
        """Opens the first USB serial port with an RP2 chip that answers PING."""
        candidates = [p.device for p in list_ports.comports() if p.vid == RP2_USB_VID]
        for device in candidates:
            try:
                conn = self._open(device)
            except Exception:
                continue
            if self._ping(conn):
                return conn
            conn.close()
        if candidates:
            raise RuntimeError(
                "No head-fixed board answers on " + ", ".join(candidates)
            )
        raise RuntimeError("No head-fixed board found among the USB serial ports")

    def _send(self, line: str) -> None:
        with self._lock:
            try:
                self.conn.write((line + "\n").encode())
            except Exception:
                self._report_error("Could not send '" + line + "' to the board")

    def _report_error(self, msg: str) -> None:
        """Keeps the error in self.error and logs it, once: if the board is
        unplugged every command fails, and must not fill the log."""
        error = log.clean_text(traceback.format_exc(), msg)
        if error != self.error:
            log.error(msg, subject=self.name, exception=traceback.format_exc())
        self.error = error

    # ── Messages from the board ───────────────────────────────────────────────

    def _reader(self) -> None:
        while self._running:
            try:
                raw = self.conn.readline()
            except Exception:
                if self._running:
                    self._report_error("Lost the connection with the board")
                time.sleep(1)
                continue
            line = raw.decode(errors="ignore").strip()
            if line:
                self._handle_line(line)

    def _handle_line(self, line: str) -> None:
        parts = line.split()
        kind = parts[0]
        if kind == "LICK" and len(parts) >= 4:
            lickport, state, board_ms = int(parts[1]), int(parts[2]), int(parts[3])
            if state == 1 and lickport in (1, 2):
                self.lick_count[lickport - 1] += 1
            if self.on_lick is not None:
                try:
                    self.on_lick(lickport, state, board_ms)
                except Exception:
                    log.error(
                        "Error in on_lick",
                        subject=self.name,
                        exception=traceback.format_exc(),
                    )
        elif kind == "STATUS":
            self._status = dict(p.split("=", 1) for p in parts[1:] if "=" in p)
            self._status_event.set()
        elif kind in ("MAG_ON", "MAG_POWER"):
            self.magnet_on = True
        elif kind == "MAG_OFF":
            self.magnet_on = False
            reason = parts[1] if len(parts) > 1 else ""
            if reason in ("TIMEOUT", "BACKUP"):
                # The firmware switched it off by itself: it was on for 10 min
                log.error(
                    "The electromagnet was on for 10 minutes and the board switched "
                    "it off (" + reason + ")",
                    subject=self.name,
                )
        elif kind == "ERR":
            log.error("The board replied: " + line, subject=self.name)
        elif kind == "BOOT":
            # The board restarted (unplugged, or its watchdog reset it): the
            # electromagnet is off and the servo stopped. Not reported right
            # after connecting: a board that was just powered sends it then.
            self.magnet_on = False
            if time.monotonic() - self._connected_at > 2:
                log.error("The board restarted (" + line + ")", subject=self.name)


def get_head_fixed() -> HeadFixed | NullHeadFixed:
    """Connects to the head-fixed board if USE_HEAD_FIXED_BOARD is ON.

    Returns:
        HeadFixed | NullHeadFixed: The connected board, or a NullHeadFixed if
        it is not used or could not be connected (with the reason in .error).
    """
    if settings.get("USE_HEAD_FIXED_BOARD") != Active.ON:
        return NullHeadFixed()
    try:
        device = HeadFixed(str(settings.get("HEAD_FIXED_PORT")).strip())
        log.info("Head-fixed board connected on " + device.port)
        return device
    except Exception:
        null_device = NullHeadFixed()
        null_device.error = log.clean_text(
            traceback.format_exc(), "Could not connect to the head-fixed board"
        )
        return null_device


head_fixed = get_head_fixed()
