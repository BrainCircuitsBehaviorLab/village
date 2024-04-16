from village.settings import settings

target = settings.get("BPOD_TARGET_FIRMWARE")

if target == "20":
    from pybpodapi.bpod.hardware.events.bpod0_7_9_fw20 import EventName
elif target == "17":
    from pybpodapi.bpod.hardware.events.bpod0_7_9_fw13 import EventName
elif target == "15":
    from pybpodapi.bpod.hardware.events.bpod0_7_9_fw13 import EventName
elif target == "13":
    from pybpodapi.bpod.hardware.events.bpod0_7_9_fw13 import EventName
elif target == "9":
    from pybpodapi.bpod.hardware.events.bpod0_7_5_fw9 import EventName
else:
    from pybpodapi.bpod.hardware.events.bpod0_7_9_fw20 import EventName
