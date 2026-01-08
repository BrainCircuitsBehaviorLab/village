# mypy: ignore-errors
import statistics
import threading
import time

from village.devices.bpod import bpod


class BpodWithLatencyTest:
    """Class to test Bpod latency by measuring round-trip time of softcodes."""

    def __init__(self, *args, **kwargs):
        """Initializes the test class with a Bpod instance and synchronization events."""
        print(1)
        self.mybpod = bpod
        print(2)

        # Events to synchronize the benchmark
        self._softcode_event = threading.Event()
        self._last_softcode_time = None

    def softcode_handler_function(self, data: int):
        """Callback executed when a softcode is received from Bpod.

        This function is used to measure the time when the softcode response arrives.
        It sets the _softcode_event to signal completion of a round trip.

        Args:
            data (int): The softcode data received (opcode).
        """
        now = time.perf_counter()
        self._last_softcode_time = now
        self._softcode_event.set()  # unlock the benchmark

        # If you want to call the original handler:
        # super().softcode_handler_function(data)


def measure_softcode_latency(bpod: BpodWithLatencyTest, n_trials: int = 100):
    """Measures the round-trip latency of softcodes sent to Bpod.

    Sends a softcode to Bpod and waits for an echo response (softcode opcode 2),
    measuring the time taken for the round trip.

    Args:
        bpod (BpodWithLatencyTest): The Bpod instance wrapper to test.
        n_trials (int, optional): Number of trials to run. Defaults to 100.
    """
    latencies = []

    time.sleep(1)

    print("todo bien")

    bpod.mybpod.connect([])

    print("que pasa")

    for i in range(n_trials):
        print("    ....a")
        bpod._softcode_event.clear()
        t0 = time.perf_counter()

        # "Ping" to Bpod
        bpod.mybpod.bpod.echo_softcode(1)

        # Wait for echo (opcode == 2)
        ok = bpod._softcode_event.wait(timeout=1.0)
        if not ok:
            print(f"Trial {i}: timeout")
            continue

        t1 = bpod._last_softcode_time
        latencies.append((t1 - t0) * 1000.0)

    if not latencies:
        print("No se obtuvo ningún dato.")
        return

    print("---- Resultados ----")
    print(f"N = {len(latencies)}")
    print(f"Min   = {min(latencies):.3f} ms")
    print(f"Max   = {max(latencies):.3f} ms")
    print(f"Media = {statistics.mean(latencies):.3f} ms")
    print(f"Mediana = {statistics.median(latencies):.3f} ms")


mybpod = BpodWithLatencyTest()
measure_softcode_latency(mybpod, 200)
