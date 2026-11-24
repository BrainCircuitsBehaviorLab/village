"""Talks to the head-fixed board from the terminal, without launching Village.

For testing the board: it prints every message the board sends (licks,
electromagnet and servo events) and sends what you type, one command per line:

    MAG 30           electromagnet on at 30 % (after a 200 ms kick)
    OFF              electromagnet off
    SERVO 90 500     servo to 90 degrees in 500 ms
    SERVO_OFF        servo pulses off
    STATUS           state of the board (raw1/raw2: lickport readings)
    HELP             list of commands

Village must not be running (the port would be busy). Run it on the Raspberry:

    python3 village/scripts/check_head_fixed.py                 # finds the board
    python3 village/scripts/check_head_fixed.py --port /dev/ttyACM1
    python3 village/scripts/check_head_fixed.py --raw 0.2       # STATUS every 0.2 s

--raw is for adjusting the sensitivity trimmers of the lickports: it prints the
readings (raw1, raw2: 0-4095) without and with licking.

Stop it with Ctrl+C or an empty line: the electromagnet is switched off.

(Not named test_*.py on purpose: pytest would collect it as a test.)
"""

import argparse
import threading
import time

import serial
from serial.tools import list_ports

# USB vendor ID of the Raspberry Pi RP2040/RP2350 chips (as in
# village/devices/head_fixed.py)
RP2_USB_VID = 0x2E8A


def ping(conn: serial.Serial) -> bool:
    """Whether the board on `conn` answers PONG to a PING within 1 s."""
    conn.reset_input_buffer()
    conn.write(b"PING\n")
    end = time.monotonic() + 1.0
    while time.monotonic() < end:
        if conn.readline().decode(errors="ignore").strip() == "PONG":
            return True
    return False


def open_board(port: str) -> serial.Serial:
    """Opens `port`, or with "auto" the first RP2 serial port answering PING."""
    if port != "auto":
        return serial.Serial(port, 115200, timeout=0.1)
    candidates = [p.device for p in list_ports.comports() if p.vid == RP2_USB_VID]
    for device in candidates:
        conn = serial.Serial(device, 115200, timeout=0.1)
        if ping(conn):
            return conn
        conn.close()
    raise SystemExit(
        "No head-fixed board found"
        + (" (no answer on " + ", ".join(candidates) + ")" if candidates else "")
    )


def main() -> None:
    """Parses the arguments, then prints the board's messages and sends the
    typed commands until Ctrl+C or an empty line."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--port", default="auto", help="serial port (default: find the board)"
    )
    parser.add_argument(
        "--raw",
        type=float,
        default=0.0,
        help="seconds between STATUS requests, printed short (0: off)",
    )
    args = parser.parse_args()

    conn = open_board(args.port)
    lock = threading.Lock()
    running = True
    start = time.monotonic()

    def send(line: str) -> None:
        with lock:
            conn.write((line + "\n").encode())

    def reader() -> None:
        while running:
            try:
                line = conn.readline().decode(errors="ignore").strip()
            except serial.SerialException:
                print("Lost the connection with the board", flush=True)
                return
            if not line or line == "PONG":
                continue
            if args.raw > 0 and line.startswith("STATUS"):
                fields = dict(p.split("=", 1) for p in line.split()[1:] if "=" in p)
                line = (
                    f"raw1={fields.get('raw1', '?'):>5}  L1={fields.get('L1', '?')}"
                    f"   raw2={fields.get('raw2', '?'):>5}  L2={fields.get('L2', '?')}"
                )
            print(f"{time.monotonic() - start:10.3f} s  {line}", flush=True)

    def poll_status() -> None:
        while running:
            send("STATUS")
            time.sleep(args.raw)

    threading.Thread(target=reader, daemon=True).start()
    if args.raw > 0:
        threading.Thread(target=poll_status, daemon=True).start()

    print(
        f"Connected to {conn.port}. Type commands (HELP for the list); "
        "Ctrl+C or an empty line to stop.",
        flush=True,
    )
    try:
        while True:
            line = input().strip()
            if not line:
                break
            send(line)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        running = False
        send("OFF")
        time.sleep(0.2)
        conn.close()
        print("\nStopped (electromagnet off).")


if __name__ == "__main__":
    main()
