from village.settings import settings

target = settings.get("BPOD_TARGET_FIRMWARE")

from village.pybpodapi.bpod.hardware.events.bpod0_7_9_fw20 import EventName
