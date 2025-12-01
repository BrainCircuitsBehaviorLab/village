# mypy: ignore-errors
import statistics
import threading
import time

from village.devices.controller import controller


class BpodWithLatencyTest:
    def __init__(self, *args, **kwargs):
        print(1)
        self.mybpod = controller
        print(2)

        # Eventos para sincronizar el benchmark
        self._softcode_event = threading.Event()
        self._last_softcode_time = None

    def softcode_handler_function(self, data: int):
        """
        Esta función se ejecuta cuando llega un softcode desde Bpod
        (opcode = 2 en el protocolo). Ideal para medir latencia.
        """
        now = time.perf_counter()
        self._last_softcode_time = now
        self._softcode_event.set()  # desbloquea el benchmark

        # Si quieres llamar al handler original:
        # super().softcode_handler_function(data)


def measure_softcode_latency(bpod: BpodWithLatencyTest, n_trials: int = 100):
    latencies = []

    time.sleep(1)

    print("todo bien")

    bpod.mybpod.connect([])

    print("que pasa")

    for i in range(n_trials):
        print("    ....a")
        bpod._softcode_event.clear()
        t0 = time.perf_counter()

        # "Ping" hacia Bpod
        bpod.mybpod.bpod.echo_softcode(1)

        # Esperamos eco (opcode == 2)
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
