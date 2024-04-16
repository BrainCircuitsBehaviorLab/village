from village.settings import settings

target = settings.get("BPOD_TARGET_FIRMWARE")

if target == "17":
    from pybpodapi.bpod.hardware.input_channels.bpod0_7_9_fw13 import InputName
elif target == "15":
    from pybpodapi.bpod.hardware.input_channels.bpod0_7_9_fw13 import InputName
elif target == "13":
    from pybpodapi.bpod.hardware.input_channels.bpod0_7_9_fw13 import InputName
elif target == "9":
    from pybpodapi.bpod.hardware.input_channels.bpod0_7_5_fw9 import InputName
else:
    from pybpodapi.bpod.hardware.input_channels.bpod0_7_5_fw9 import InputName
