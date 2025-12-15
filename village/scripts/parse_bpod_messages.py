import re
from typing import Any


def parse_input_to_tuple_override(msg: str) -> tuple[str, int, int]:
    """Parses a Bpod input message string into a structured tuple.

    Args:
        msg (str): The input message string (e.g., 'Port1In').

    Returns:
        tuple[str, int, int]: A tuple (type, channel, value).

    Raises:
        ValueError: If the message format is unrecognized.
    """

    # Pattern for "Port#In" and "Port#Out" (where # is 1-9)
    port_pattern = re.compile(r"Port([0-9])(In|Out)")

    # Pattern for "PA1_Port#In" and "PA1_Port#Out" (where # is 1-9)
    pa1_port_pattern = re.compile(r"PA1_Port([0-9])(In|Out)")

    # Pattern for "BNC#High" and "BNC#Low" (where # is 1-9)
    bnc_pattern = re.compile(r"BNC([0-9])(High|Low)")

    # Pattern for "SerialX_Y" messages (where X is 1-9 and Y is 1-99)
    serial_pattern = re.compile(r"Serial([0-9])_([0-9][0-9]?)")

    if port_match := port_pattern.match(msg):
        channel, state = port_match.groups()
        value = 1 if state == "In" else 0
        return ("Port", int(channel), value)

    elif pa1_port_match := pa1_port_pattern.match(msg):
        channel, state = pa1_port_match.groups()
        value = 1 if state == "In" else 0
        return ("PA1_Port", int(channel), value)

    elif bnc_match := bnc_pattern.match(msg):
        channel, state = bnc_match.groups()
        value = 3 if state == "High" else 0
        return ("BNC", int(channel), value)

    elif serial_match := serial_pattern.match(msg):
        channel, val = serial_match.groups()
        return ("Serial", int(channel), int(val))

    else:
        raise ValueError(f"Unrecognized message format: {msg}")


def parse_output_to_tuple_override(
    message: str | tuple[str, int]
) -> tuple[str, Any, int]:
    """Parses a Bpod output message into a structured tuple.

    Args:
        message (str | tuple): The output message to parse.

    Returns:
        tuple[str, Any, int]: A tuple (type, channel, value).

    Raises:
        ValueError: If the message format is unrecognized.
    """
    # Convert the message to string if it's a tuple
    msg = str(message)

    # Pattern for ("PWMX", Y) messages (where X is 1-9 and Y is 0-255)
    pwm_pattern = re.compile(r"\('PWM([1-9])',\s*([0-9]|[0-9][0-9]{1,2})\)")

    # Pattern for "ValveXOff" messages (where X is 1-8)
    valve_off_pattern = re.compile(r"Valve([1-8])Off")

    # Pattern for "ValveX" messages (where X is 1-8)
    valve_pattern = re.compile(r"Valve([1-8])")

    # Pattern for "BNCXY" (where X is 1-2 and Y is High or Low)
    bnc_pattern = re.compile(r"BNC([0-9])(High|Low)")

    # Pattern for ("SerialX", Y) messages (where X is 1-9 and Y is 0-99)
    serial_pattern = re.compile(r"\('Serial([0-9])',\s*([0-9][0-9]?)")

    if pwm_match := pwm_pattern.match(msg):
        channel, val = pwm_match.groups()
        return ("PWM", int(channel), int(val))

    elif valve_off_match := valve_off_pattern.match(msg):
        channel = valve_off_match.group(1)
        return ("Valve", int(channel), 0)

    elif valve_match := valve_pattern.match(msg):
        channel = valve_match.group(1)
        return ("Valve", int(channel), 1)

    elif bnc_match := bnc_pattern.match(msg):
        channel, state = bnc_match.groups()
        value = 3 if state == "High" else 0
        return ("BNC", int(channel), value)

    elif serial_match := serial_pattern.match(msg):
        channel, val = serial_match.groups()
        return ("Serial", int(channel), int(val))

    else:
        raise ValueError(f"Unrecognized message format: {msg}")


def parse_output_to_tuple(val: str | tuple[str, int]) -> tuple:
    """Parses typical Bpod output strings or tuples into standardized tuples.

    Args:
        val (str | tuple): The output value/message.

    Returns:
        tuple: (Base, Info) parsed structure.

    Raises:
        ValueError: If the input format is invalid.
    """
    if isinstance(val, tuple):
        return val
    else:
        patterns = [
            (r"^Valve(\d+)$", "Valve", lambda groups: int(groups[0])),
            (
                r"^BNC(\d+)(High|Low)$",
                lambda groups: f"BNC{groups[0]}",
                lambda groups: 3 if groups[1] == "High" else 0,
            ),
            (r"^SoftCode(\d+)$", "SoftCode", lambda groups: int(groups[0])),
            (
                r"^GlobalTimer(\d+)Trig$",
                "GlobalTimerTrig",
                lambda groups: int(groups[0]),
            ),
            (
                r"^GlobalTimer(\d+)Cancel$",
                "GlobalTimerCancel",
                lambda groups: int(groups[0]),
            ),
            (
                r"^GlobalCounter(\d+)Reset$",
                "GlobalCounterReset",
                lambda groups: int(groups[0]),
            ),
        ]

        for pattern, prefix, suffix_fn in patterns:
            match = re.match(pattern, val)
            if match:
                groups = match.groups()
                base = prefix(groups) if callable(prefix) else prefix
                suffix = suffix_fn(groups)
                return (base, suffix)

        raise ValueError(f"Bad output_state: {val}")

