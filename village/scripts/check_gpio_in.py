"""Watches the GPIO input pin and prints every change, without launching Village.

For testing what is wired to GPIO_IN (a switch, a TTL, ...). It uses the same
logic as village/devices/gpio.py: a gpiozero DigitalInputDevice with the
internal pull-down, and callbacks on OFF -> ON (trigger_on) and ON -> OFF
(trigger_off).

Village must not be running (the pin would be busy). Run it on the Raspberry:

    python3 village/scripts/check_gpio_in.py            # pin 26, like GPIO_IN
    python3 village/scripts/check_gpio_in.py --pin 17
    python3 village/scripts/check_gpio_in.py --pull up  # internal pull-up

Stop it with Ctrl+C.

Each change is printed with the time since the previous one: a mechanical
switch usually bounces, which shows up as several changes a few ms apart.

(Not named test_*.py on purpose: pytest would collect it as a test.)
"""

import argparse
import signal
import time


def main() -> None:
    """Parses the arguments and watches the pin until Ctrl+C."""
    from gpiozero import DigitalInputDevice

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--pin",
        type=int,
        default=26,
        help="BCM pin number (default: 26, as GPIO_IN)",
    )
    parser.add_argument(
        "--pull",
        choices=["down", "up", "none"],
        default="down",
        help="internal resistor (default: down, as in gpio.py)",
    )
    parser.add_argument(
        "--status",
        type=float,
        default=5.0,
        help="seconds between status lines with the current level (0: off)",
    )
    args = parser.parse_args()

    # gpiozero: pull_up=False -> pull-down, active when HIGH (as in gpio.py).
    # pull_up=True -> pull-up, active when LOW. pull_up=None -> no internal
    # resistor (needs an external one), active_state chosen explicitly.
    if args.pull == "down":
        device = DigitalInputDevice(args.pin, pull_up=False)
    elif args.pull == "up":
        device = DigitalInputDevice(args.pin, pull_up=True)
    else:
        device = DigitalInputDevice(args.pin, pull_up=None, active_state=True)

    start = time.monotonic()
    last_change = start
    changes = 0

    def level() -> str:
        """The raw electrical level of the pin."""
        return "HIGH" if device.pin.state else "LOW"

    def report(name: str) -> None:
        nonlocal last_change, changes
        now = time.monotonic()
        changes += 1
        print(
            f"{now - start:10.3f} s  {name:<11} level={level():<4}  "
            f"{(now - last_change) * 1000:9.1f} ms since previous change  "
            f"(#{changes})",
            flush=True,
        )
        last_change = now

    device.when_activated = lambda: report("trigger_on")  # OFF -> ON
    device.when_deactivated = lambda: report("trigger_off")  # ON -> OFF

    print(
        f"Watching BCM pin {args.pin}, pull-{args.pull}. "
        f"Now: level={level()}, {'ON' if device.value else 'OFF'}. Ctrl+C to stop.",
        flush=True,
    )

    try:
        if args.status > 0:
            while True:
                time.sleep(args.status)
                print(
                    f"{time.monotonic() - start:10.3f} s  status      "
                    f"level={level():<4}  {'ON' if device.value else 'OFF'}, "
                    f"{changes} changes so far",
                    flush=True,
                )
        else:
            signal.pause()
    except KeyboardInterrupt:
        pass
    finally:
        device.close()
        print(f"\nStopped. {changes} changes.")


if __name__ == "__main__":
    main()
