import threading
import time
from unittest.mock import MagicMock

import pytest

from village.devices import head_fixed as head_fixed_module
from village.devices.head_fixed import HeadFixed


class FakeSerial:
    """Stands in for the board's serial port: answers PING and STATUS like the
    firmware, and lets the test push unsolicited lines."""

    def __init__(self, answers: bool = True) -> None:
        self.port = "/dev/fake"
        self.answers = answers
        self.written: list[str] = []
        self._lines: list[bytes] = []
        self._cond = threading.Condition()

    def push(self, line: str) -> None:
        with self._cond:
            self._lines.append((line + "\r\n").encode())
            self._cond.notify()

    def write(self, data: bytes) -> int:
        line = data.decode().strip()
        self.written.append(line)
        if self.answers and line == "PING":
            self.push("PONG")
        elif self.answers and line == "STATUS":
            self.push("STATUS mag=OFF power=0.0 servo=OFF L1=0 L2=0 raw1=27 raw2=30")
        return len(data)

    def readline(self) -> bytes:
        with self._cond:
            if not self._lines:
                self._cond.wait(0.05)
            return self._lines.pop(0) if self._lines else b""

    def reset_input_buffer(self) -> None:
        with self._cond:
            self._lines.clear()

    def close(self) -> None:
        return


@pytest.fixture
def board(monkeypatch):
    fake = FakeSerial()
    monkeypatch.setattr(head_fixed_module, "log", MagicMock())
    monkeypatch.setattr(HeadFixed, "_open", staticmethod(lambda port: fake))
    device = HeadFixed("/dev/fake")
    yield device, fake
    device._running = False


def wait_until(condition, timeout: float = 1.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


class TestConnection:
    def test_connects_when_the_board_answers(self, board):
        device, fake = board
        assert device.port == "/dev/fake"
        assert device.error == ""
        assert fake.written[0] == "PING"

    def test_raises_when_the_board_does_not_answer(self, monkeypatch):
        monkeypatch.setattr(
            HeadFixed, "_open", staticmethod(lambda port: FakeSerial(answers=False))
        )
        with pytest.raises(RuntimeError):
            HeadFixed("/dev/fake")


class TestCommands:
    def test_magnet(self, board):
        device, fake = board
        device.magnet(30)
        assert fake.written[-1] == "MAG 30.0"

    def test_magnet_zero_switches_off(self, board):
        device, fake = board
        device.magnet(0)
        assert fake.written[-1] == "OFF"

    def test_servo(self, board):
        device, fake = board
        device.servo(90, 500)
        assert fake.written[-1] == "SERVO 90.0 500"

    def test_servo_negative_time_is_instant(self, board):
        device, fake = board
        device.servo(45, -10)
        assert fake.written[-1] == "SERVO 45.0 0"

    def test_servo_off(self, board):
        device, fake = board
        device.servo_off()
        assert fake.written[-1] == "SERVO_OFF"

    def test_status(self, board):
        device, _ = board
        status = device.status()
        assert status is not None
        assert status["raw1"] == "27"
        assert status["servo"] == "OFF"

    def test_close_switches_the_magnet_off(self, board):
        device, fake = board
        device.close()
        assert fake.written[-1] == "OFF"


class TestMessages:
    def test_licks_are_counted_on_start_only(self, board):
        device, fake = board
        calls = []
        device.on_lick = lambda port, state, t: calls.append((port, state, t))
        fake.push("LICK 1 1 100")
        fake.push("LICK 1 0 150")
        fake.push("LICK 2 1 200")
        assert wait_until(lambda: len(calls) == 3)
        assert device.lick_count == [1, 1]
        assert calls[0] == (1, 1, 100)

    def test_magnet_state(self, board):
        device, fake = board
        fake.push("MAG_ON 30.0 1000 remaining_ms=600000")
        assert wait_until(lambda: device.magnet_on)
        fake.push("MAG_OFF CMD 2000")
        assert wait_until(lambda: not device.magnet_on)

    def test_timeout_is_logged(self, board):
        device, fake = board
        device.magnet_on = True
        fake.push("MAG_OFF TIMEOUT 600000")
        assert wait_until(lambda: head_fixed_module.log.error.called)
        assert not device.magnet_on

    def test_a_normal_off_is_not_logged(self, board):
        device, fake = board
        fake.push("MAG_OFF CMD 2000")
        fake.push("PONG")  # once this is read, the line before was handled
        time.sleep(0.2)
        assert not head_fixed_module.log.error.called
