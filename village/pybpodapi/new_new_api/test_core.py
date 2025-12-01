import sys

from bpod import Bpod


def test_core():
    port = "/dev/controller"
    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"Testing new_new_api.Bpod on {port}...")

    bpod = Bpod(port)
    if bpod.connect():
        print("SUCCESS: Connected and initialized!")
        print(f"Firmware: {bpod.firmware_version}")
        print(f"Hardware: {bpod.hardware_info}")
        bpod.close()
    else:
        print("FAILURE: Could not connect.")


if __name__ == "__main__":
    test_core()
