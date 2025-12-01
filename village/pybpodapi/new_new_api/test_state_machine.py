import sys

from bpod import Bpod
from state_machine import StateMachine


def test_state_machine():
    port = "/dev/controller"
    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"Testing State Machine on {port}...")

    bpod = Bpod(port)
    if not bpod.connect():
        print("Failed to connect.")
        return

    try:
        # Create State Machine
        sma = StateMachine(bpod)

        # State 0: LED ON, Timer 1s -> State 1
        # Using PWM1 for LED (assuming Port 1 has an LED)
        sma.add_state(
            name="State1",
            timer=1.0,
            state_change_conditions={"Tup": "State2"},
            output_actions=[("PWM1", 255)],
        )

        # State 1: LED OFF, Timer 1s -> Exit
        sma.add_state(
            name="State2",
            timer=1.0,
            state_change_conditions={"Tup": "exit"},
            output_actions=[("PWM1", 0)],
        )

        # Send State Machine
        if bpod.send_state_machine(sma):
            print("State machine sent. Running now (Ctrl+C to stop)...")
            bpod.run_state_machine()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        bpod.close()


if __name__ == "__main__":
    test_state_machine()
