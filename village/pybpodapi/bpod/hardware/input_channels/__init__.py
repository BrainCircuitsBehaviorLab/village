from village.app.settings import settings

target = settings.get("BPOD_TARGET_FIRMWARE")

if target == "17":
    from village.pybpodapi.bpod.hardware.input_channels.bpod0_7_9_fw13 import InputName
elif target == "15":
    from village.pybpodapi.bpod.hardware.input_channels.bpod0_7_9_fw13 import InputName
elif target == "13":
    from village.pybpodapi.bpod.hardware.input_channels.bpod0_7_9_fw13 import InputName
elif target == "9":
    from village.pybpodapi.bpod.hardware.input_channels.bpod0_7_5_fw9 import InputName
else:
    from village.pybpodapi.bpod.hardware.input_channels.bpod0_7_5_fw9 import InputName
