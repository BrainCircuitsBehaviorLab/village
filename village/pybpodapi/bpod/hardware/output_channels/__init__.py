from village.app.settings import settings

target = settings.get("BPOD_TARGET_FIRMWARE")

from village.pybpodapi.bpod.hardware.output_channels.bpod0_7_5_fw9 import (
    OutputChannel,
)
