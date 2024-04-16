from village.settings import settings

target = settings.get("BPOD_TARGET_FIRMWARE")

if target == "20":
    from pybpodapi.bpod.hardware.output_channels.bpod0_7_9_fw20 import OutputChannel
elif target == "17":
    from pybpodapi.bpod.hardware.output_channels.bpod0_7_9_fw13 import OutputChannel
elif target == "15":
    from pybpodapi.bpod.hardware.output_channels.bpod0_7_9_fw13 import OutputChannel
elif target == "13":
    from pybpodapi.bpod.hardware.output_channels.bpod0_7_9_fw13 import OutputChannel
elif target == "9":
    from pybpodapi.bpod.hardware.output_channels.bpod0_7_5_fw9 import OutputChannel
else:
    from pybpodapi.bpod.hardware.output_channels.bpod0_7_5_fw9 import OutputChannel
